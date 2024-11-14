import base64
from nicegui import ui, app
import pandas as pd
import mimetypes
import asyncio
import os
import logging
from pathlib import Path

from config import config
from components.shared import StaticPage
from utils.helpers import s3_storage_adapter, dynamo_adapter
from models import ManagedState
from services.rag.AgenticRag import AgenticRAG


class FileManagerState(ManagedState):
    def __init__(self):
        super().__init__("file_manager_state")
        # Initialize all state variables
        self.update(
            {
                "current_path_parts": [],
                "header_text": "File Manager - /",
                "folder_depth": 0,
                "selected_company_id": None,
                "company_information": None,
                "file_preview": None,
                "account_information": None,
                "tab_view": "chat",
                "file_type": None,
                "file_key": None,
            }
        )


class FileManagerPage(StaticPage):
    def __init__(self, storage_manager):
        super().__init__(
            page_title="File Manager",
            page_route="/file-manager",
            page_description="File Manager",
            storage_manager=storage_manager,
        )
        # Setup logging
        self.setup_logging()

        self.s3_adapter = s3_storage_adapter(self.storage_manager)
        self.dynamo_adapter = dynamo_adapter(config.aws_companies_table_name)
        self.state = FileManagerState()
        self.agentic_rag = None
        self._previous_path = None  # Track previous path
        self.directory_has_files = False  # Initialize directory files flag

    def setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Configure logger
        self.logger = logging.getLogger("FileManager")
        self.logger.setLevel(logging.INFO)

        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # Create formatters
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_formatter = logging.Formatter("%(levelname)s - %(message)s")

        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_dir / "file_manager.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(file_formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)

        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        self.logger.info("FileManager logging setup completed")

    @property
    def current_path(self):
        return "/".join(self.current_path_parts) + (
            "/" if self.current_path_parts else ""
        )

    @property
    def current_path_parts(self):
        return self.state.get("current_path_parts")

    @current_path_parts.setter
    def current_path_parts(self, value):
        self.state.set("current_path_parts", value)

    @property
    def header_text(self):
        return self.state.get("header_text")

    @header_text.setter
    def header_text(self, value):
        self.state.set("header_text", value)

    @property
    def folder_depth(self):
        return self.state.get("folder_depth")

    @folder_depth.setter
    def folder_depth(self, value):
        self.state.set("folder_depth", value)

    @property
    def selected_company_id(self):
        return self.state.get("selected_company_id")

    @selected_company_id.setter
    def selected_company_id(self, value):
        self.state.set("selected_company_id", value)

    @property
    def tab_view(self):
        return self.state.get("tab_view")

    @tab_view.setter
    def tab_view(self, value):
        self.state.set("tab_view", value)

    @property
    def file_preview(self):
        return self.state.get("file_preview")

    @file_preview.setter
    def file_preview(self, value):
        self.state.set("file_preview", value)

    @property
    def file_type(self):
        return self.state.get("file_type")

    @file_type.setter
    def file_type(self, value):
        self.state.set("file_type", value)

    @property
    def file_key(self):
        return self.state.get("file_key")

    @file_key.setter
    def file_key(self, value):
        self.state.set("file_key", value)

    def get_company_info(self, company_id):
        # Format the key correctly for DynamoDB
        key = {"company_id": {"S": company_id}}
        company_info = self.dynamo_adapter.get_item(key)
        return company_info

    def render_csv_preview(self):
        """
        Renders the CSV file preview using AgGrid in the right-hand column.
        """
        if self.file_preview is not None:
            data = self.file_preview.to_dict(orient="records")
            columns = [
                {"headerName": col, "field": col, "hide": False}
                for col in self.file_preview.columns
            ]

            # Render the AgGrid table and the column visibility controls
            with ui.column().style("width: 100%; height: 100%;"):
                with ui.row().style(
                    "display: flex; align-items: center; width: 100%; padding: 0.5rem; justify-content: flex-end;"
                ):
                    with ui.dialog() as dialog:
                        with ui.card().style(
                            "width: 50rem; height: auto; max-height: 90rem;"
                        ):
                            ui.label("Select Columns").classes("text-lg text-bold")
                            with ui.grid(columns=2).style("overflow-y: auto;"):
                                for index, col in enumerate(columns):
                                    ui.switch(
                                        col["headerName"],
                                        value=not col["hide"],
                                        on_change=lambda e, col=col: update_column_visibility(
                                            col, e.value
                                        ),
                                    )
                    ui.button(
                        "columns", icon="s_view_column", on_click=lambda: dialog.open()
                    )

                table = ui.aggrid(
                    {
                        "columnDefs": columns,
                        "rowData": data,
                        "defaultColDef": {
                            "sortable": True,
                            "filter": True,
                            "resizable": True,
                        },
                        "pagination": True,
                        "paginationPageSize": 100,
                    }
                ).style("width: 100%; height: 100%;")

                def update_column_visibility(col, is_visible):
                    col["hide"] = not is_visible
                    table.update()

    def render_pdf_preview(self):
        """
        Renders the PDF file preview using a simple HTML5 approach.
        """
        with ui.column().style("width: 100%; height: 100%;"):
            if self.file_preview:
                base64_pdf = base64.b64encode(self.file_preview).decode("utf-8")
                ui.html(
                    f"""
                    <embed src="data:application/pdf;base64,{base64_pdf}"
                           type="application/pdf"
                           width="100%"
                           height="100%"
                           style="border: none;">
                """
                ).style("width: 100%; height: 100%;")
            else:
                ui.label(
                    f"Error loading PDF preview for file: {self.file_key}"
                ).classes("text-red-500")
                ui.label("Please check the server logs for more information.").classes(
                    "text-red-500"
                )

    def render_unsupported_file_type(self):
        """
        Renders a message for unsupported file types.
        """
        with ui.column().style(
            "width: 100%; height: 100%; justify-content: center; align-items: center;"
        ):
            ui.label(
                "Unsupported file type. Please download the file to view its contents."
            ).classes("text-lg text-bold")

    @ui.refreshable
    def DirectoryViewer(self):
        def navigate_to_directory(directory_name):
            """
            Navigates to a specified directory within the current path.
            """
            # Strip any slashes and ensure we only add the relative directory name
            directory_name = directory_name.strip("/")

            # Append the directory name only if it is not already present
            if (
                not self.current_path_parts
                or self.current_path_parts[-1] != directory_name
            ):
                self.current_path_parts.append(directory_name)

            # Render the updated contents of the new path
            # Check for files in new directory
            print(self.directory_has_files)
            self.check_directory_for_files()
            self.folder_depth += 1
            self.InformationViewer.refresh()
            self.DirectoryViewer.refresh()

        def navigate_back():
            """
            Navigates back to the previous directory.
            """
            if self.current_path_parts:
                self.current_path_parts.pop()
            else:
                print("You are already at the root directory.")

            # Render the updated contents of the new path
            self.check_directory_for_files()
            self.folder_depth -= 1
            self.InformationViewer.refresh()
            self.DirectoryViewer.refresh()

        def reset_to_root():
            """
            Resets the current path to the root directory.
            """
            self.current_path_parts = []
            self.folder_depth = 0
            self.DirectoryViewer.refresh()

        def _handle_directory_click(directory_name):
            """
            Handles clicking on a directory.
            """
            # Navigate to the clicked directory
            if self.folder_depth == 0:
                self.selected_company_id = directory_name
            navigate_to_directory(directory_name)

        def _load_file_preview(file_key):
            self.tab_view = "preview"
            self.file_key = file_key  # Store the file key for error reporting
            mime_type, _ = mimetypes.guess_type(file_key)
            if mime_type == "application/pdf":
                self.file_preview = self.s3_adapter.get_file_content(
                    bucket_name=config.aws_s3_client_bucket, file_key=file_key
                )
                self.file_type = "pdf"
            elif mime_type == "text/csv":
                self.file_preview = self.s3_adapter.read_csv_to_dataframe(
                    bucket_name=config.aws_s3_client_bucket, file_key=file_key
                )
                self.file_type = "csv"
            else:
                self.file_type = "unsupported"
            self.FilePreviewer.refresh()

        def _handle_download_click(file_key):
            """
            Handles clicking on the download button for a file.
            """
            bucket_name = config.aws_s3_client_bucket
            file_name = file_key.split("/")[-1]

            # Download the file from S3
            response = self.s3_adapter.s3_client.get_object(
                Bucket=bucket_name, Key=file_key
            )
            file_content = response["Body"].read()

            # Use NiceGUI to prepare a download for the user's browser
            ui.download(file_content, file_name)

        with ui.card().style("width:100%;height:86vh;"):
            with ui.scroll_area().style("width:100%;height:100%;"):
                with ui.list().props("bordered separator").style(
                    "width:100%;height:100%"
                ):
                    # Update header text with the current path using the property
                    ui.item_label(f"{self.header_text}{self.current_path}").props(
                        "header"
                    ).classes("text-bold text-lg")
                    ui.separator()

                    # Add Back button if not at the root
                    if self.current_path_parts:
                        with ui.item(on_click=navigate_back):
                            with ui.item_section().props("side"):
                                ui.icon("arrow_back").props("size=small")
                            with ui.item_section():
                                ui.label(".. (Back)").classes("font-medium")
                        ui.separator()

                    # List current directory objects using the current path property
                    objects = self.s3_adapter.list_objects(
                        bucket_name=config.aws_s3_client_bucket,
                        current_path=self.current_path,
                    )

                    if objects:
                        # List directories
                        for directory in objects["directories"]:
                            relative_directory = directory.strip("/").split("/")[-1]
                            with ui.item(
                                on_click=lambda d=relative_directory: _handle_directory_click(
                                    d
                                )
                            ):
                                with ui.item_section().props("side"):
                                    ui.icon("folder").props("size=small").classes(
                                        "text-yellow-600"
                                    )
                                with ui.item_section():
                                    ui.label(relative_directory).classes(
                                        "font-semibold"
                                    )
                            ui.separator()

                        # List files
                        for file_key in objects["files"]:
                            # Get just the filename for display
                            display_name = os.path.basename(file_key)

                            # Get metadata for each file
                            file_metadata = self.s3_adapter.get_file_metadata(
                                bucket_name=config.aws_s3_client_bucket,
                                file_key=file_key,
                            )
                            file_size = file_metadata.get("Size", "Unknown Size")
                            last_modified = file_metadata.get(
                                "LastModified", "Unknown Date"
                            )

                            with ui.item():
                                with ui.item_section().props("side"):
                                    ui.icon("description").props("size=small").classes(
                                        "text-green-600"
                                    )
                                with ui.item_section():
                                    # Use display_name for showing, but keep full path for functionality
                                    ui.item_label(display_name).classes("text-gray-800")
                                    ui.item_label(
                                        f"Size: {file_size}, Modified: {last_modified}"
                                    ).classes("text-sm text-gray-500").props("caption")
                                with ui.item_section().props("top side"):
                                    ui.button(
                                        icon="s_visibility",
                                        on_click=lambda file_key=file_key: _load_file_preview(
                                            file_key
                                        ),
                                    ).props("flat dense round")
                                with ui.item_section().props("top side"):
                                    ui.button(
                                        icon="download",
                                        on_click=lambda file_key=file_key: _handle_download_click(
                                            file_key
                                        ),
                                    ).props("flat dense round")

    @ui.refreshable
    def FilePreviewer(self):
        if self.file_type == "csv":
            self.render_csv_preview()
        elif self.file_type == "pdf":
            self.render_pdf_preview()
        else:
            self.render_unsupported_file_type()

    def render_none_selected(self):
        with ui.column().style("width: 100%; height: 100%;"):
            with ui.row().style(
                "display:flex;width:100%;height:100%;justify-content:center;align-items:center;"
            ):
                with ui.card().style(
                    "display:flex;flex-direction:column;justify-content:center;align-items:center"
                ):
                    ui.label("No company selected").classes("text-lg text-bold")

    def render_none_found(self):
        with ui.column().style("width: 100%; height: 100%;"):
            with ui.row().style(
                "display:flex;width:100%;height:100%;justify-content:center;align-items:center;"
            ):
                with ui.card().style(
                    "display:flex;flex-direction:column;justify-content:center;align-items:center"
                ):
                    ui.label("No company Information found").classes(
                        "text-lg text-bold"
                    )

    @ui.refreshable
    def InformationViewer(self):
        print(self.folder_depth)
        if self.folder_depth == 0:
            with ui.column().style("width:100%;height:100%"):
                recent_uploads = self.s3_adapter.get_recent_uploads(
                    bucket_name="nda-client-storage-v1", limit=30
                )
                with ui.card().style("width:100%;height:100%"):
                    ui.label("Recent Uploads").classes(
                        "text-lg font-bold mb-1 border-b w-full"
                    )
                    with ui.scroll_area().style("height:100%"):
                        for file_path, last_modified in recent_uploads:
                            ui.separator()
                            file_name = file_path.split("/")[
                                -1
                            ]  # Extract just the file name
                            with ui.row().classes("items-center w-full"):
                                ui.icon("insert_drive_file").classes(
                                    "text-blue-500 mr-2"
                                )
                                ui.label(file_name).classes("text-sm")
                                ui.space()
                                ui.label(
                                    last_modified.strftime("%Y-%m-%d %H:%M")
                                ).classes("text-xs text-gray-500 ml-auto")
        elif self.folder_depth == 1:
            self.CompanyInformation()
        elif self.folder_depth == 2:
            self.CompanyInformation()
        elif self.folder_depth == 3:
            self.CompanyInformation()
        elif self.folder_depth == 4:
            self.AccountInformation()
        else:
            self.render_none_found()

    def initialize_rag(self):
        """Initialize or reinitialize AgenticRAG when needed"""
        if self.folder_depth == 4:
            current_path = self.current_path.rstrip("/")

            # Check if we need to reinitialize due to path change
            if self._previous_path != current_path:
                # Reset the RAG instance
                if self.agentic_rag is not None:
                    self.agentic_rag = None

                # Create new instance with current path
                bucket_name = config.aws_s3_client_bucket
                self.agentic_rag = AgenticRAG(
                    bucket_name=bucket_name, directory_key=current_path
                )
                self._previous_path = current_path
                return True

            # Initialize if not exists
            elif self.agentic_rag is None:
                bucket_name = config.aws_s3_client_bucket
                self.agentic_rag = AgenticRAG(
                    bucket_name=bucket_name, directory_key=current_path
                )
                self._previous_path = current_path
                return True

        return False

    def AccountInformation(self):
        # Initialize/reinitialize RAG when entering this view
        self.initialize_rag()

        with ui.tabs() as tabs:
            ui.tab("chat", label="Chat", icon="o_chat")
            ui.tab("preview", label="File Preview", icon="o_preview")
        with ui.tab_panels(tabs, value=self.tab_view).style(
            "width:100%;height:100%;"
        ).bind_value(self, "tab_view"):
            with ui.tab_panel("chat"):
                """Render the chat interface with optimized loading"""
                ui.query(".q-page").classes("flex flex-col")
                ui.query(".nicegui-content").classes("w-full flex-grow")

                with ui.column().classes("w-full max-w-3xl mx-auto flex-grow"):
                    self.scroll_area = ui.scroll_area().classes("w-full flex-grow")

                    with self.scroll_area:
                        self.message_container = ui.column().classes("w-full p-4")
                        with self.message_container:
                            if self.folder_depth != 4:
                                ui.chat_message(
                                    text="Please navigate to a document folder to use the chat feature.",
                                    name="Assistant",
                                    sent=False,
                                )
                            else:
                                ui.chat_message(
                                    text="Hi! You can start asking questions about the documents in this folder.",
                                    name="Assistant",
                                    sent=False,
                                )

                    async def send(text_input) -> None:
                        if not text_input.value:
                            return

                        if self.folder_depth != 4:
                            with self.message_container:
                                ui.chat_message(
                                    text="Please navigate to a document folder to use the chat feature.",
                                    name="Assistant",
                                    sent=False,
                                )
                            text_input.value = ""
                            return

                        question = text_input.value
                        text_input.value = ""

                        with self.message_container:
                            ui.chat_message(text=question, name="You", sent=True)
                            response_message = ui.chat_message(
                                name="Assistant", sent=False
                            )
                            spinner = ui.spinner(type="dots")

                        try:
                            if not self.agentic_rag:
                                self.initialize_rag()

                            result = await self.agentic_rag.process_query(question)
                            response_message.clear()
                            with response_message:
                                ui.markdown(result["response"])
                        except Exception as e:
                            response_message.clear()
                            with response_message:
                                ui.markdown(f"An error occurred: {str(e)}")
                        finally:
                            spinner.delete()
                            self.scroll_area.scroll_to(percent=1.0)

                    with ui.row().classes("w-full my-2"):
                        with ui.column().classes("flex flex-1"):
                            text_input = (
                                ui.input(placeholder="Message")
                                .props("outlined rounded")
                                .classes("w-full")
                            )
                            text_input.on(
                                "keydown.enter",
                                lambda: asyncio.create_task(send(text_input)),
                            )
                        with ui.column().classes(
                            "flex items-center justify-center"
                        ).style("height:100%"):
                            ui.button(
                                icon="send",
                                on_click=lambda: asyncio.create_task(send(text_input)),
                            ).props("dense round")
            with ui.tab_panel("preview").style("width:100%;height:100%"):
                self.FilePreviewer()

    def CompanyInformation(self):
        company_info = self.get_company_info(self.selected_company_id)
        if company_info is None:
            self.render_none_found()
            return

        with ui.column().style("width: 100%; height: 100%;"):
            with ui.row().style("display:flex;width:100%;"):
                with ui.card().style("display:flex;flex-direction:column;gap:0.3rem;"):
                    with ui.column().style(
                        "display:flex;flex-direction:column;gap:0.3rem;"
                    ):
                        ui.label(company_info["company_name"]).classes(
                            "text-lg text-bold"
                        )
                        with ui.row().style("display:flex;width:100%;gap:0.2rem"):
                            ui.label("ID:").props("caption").style("font-size:0.7rem;")
                            ui.label(company_info["company_id"]).style(
                                "font-size:0.7rem;"
                            )
                ui.space()
                with ui.column().style(
                    "padding:0.5rem;display:flex;flex-direction:column;gap:0.3rem;"
                ):
                    ui.label(company_info["company_address_01"])
                    ui.label(company_info["company_address_02"])
                    ui.label(
                        f'{company_info["company_city"]}, {company_info["company_state"]} {company_info["company_zip"]}'
                    )
            ui.separator().classes("w-full")
            with ui.row().style("display:flex;width:100%;"):
                with ui.column().style(
                    "padding:0.5rem;display:flex;flex-direction:column;gap:0.3rem;"
                ):
                    ui.label("Company Phone")
                    ui.label(company_info["company_phone"])
            with ui.row().style("display:flex;width:100%;height:100%;"):
                with ui.list().props("bordered separator").classes("w-full"):
                    ui.item_label("Contacts").props("header").classes(
                        "text-bold text-lg"
                    )
                    ui.separator()
                    for contact in company_info["company_contacts"]:
                        first_name = contact.get("contact_first_name", "Unknown")
                        last_name = contact.get("contact_last_name", "Unknown")
                        title = contact.get("contact_title", "Unknown")
                        phone = contact.get("contact_phone", "Unknown")
                        email = contact.get("contact_email", "Unknown")
                        with ui.item():
                            with ui.item_section().props("side"):
                                ui.icon("person").props("size=small").classes(
                                    "text-blue-600"
                                )
                            with ui.item_section():
                                ui.item_label(f"{first_name} {last_name}").classes(
                                    "font-semibold"
                                )
                                ui.item_label(title).props("caption")
                            with ui.item_section().props("top side"):
                                ui.button(
                                    icon="email",
                                    on_click=lambda: ui.notify(
                                        f"Email: {email}\nPhone: {phone}"
                                    ),
                                ).props("flat dense round")
                        ui.separator()

    def check_directory_for_files(self) -> bool:
        """Check if current directory contains any files"""
        try:
            self.logger.info(f"Checking directory for files: {self.current_path}")
            objects = self.s3_adapter.list_objects(
                bucket_name=config.aws_s3_client_bucket,
                current_path=self.current_path,
            )

            # Get files from the response
            files = objects.get("files", [])

            # Log what we found
            self.logger.info(f"Found {len(files)} files in directory")
            if files:
                self.logger.info(f"Files found: {[os.path.basename(f) for f in files]}")

            # Update and return status
            self.directory_has_files = len(files) > 0
            self.logger.info(f"Directory has files: {self.directory_has_files}")

            return self.directory_has_files

        except Exception as e:
            self.logger.error(
                f"Error checking directory for files: {str(e)}", exc_info=True
            )
            self.directory_has_files = False
            return False

    def content(self):
        with ui.grid(columns=2).style("width: 100%; height: 86vh;"):
            with ui.column().classes("w-full h-[100%]"):
                self.DirectoryViewer()
            with ui.card().style(
                "display:flex; flex-direction:column; width:100%; height:100%; border:1px solid #e2e8f0; border-radius:0.5rem; box-shadow: 0 0 5px 0 rgba(0,0,0,0.1);"
            ):
                self.InformationViewer()


def file_manager_page(storage_manager):
    page = FileManagerPage(storage_manager)
    page.render()
