from nicegui import ui
from core import StandardPage

import base64
import pandas as pd
import mimetypes
from pathlib import Path
from io import StringIO

from config import config

from middleware.s3 import S3Middleware
from middleware.dynamo import DynamoMiddleware
from modules.list_manager import ListManager

from modules import StateManager


class SharedState:
    def __init__(self):
        self.current_company_id = None
        self.current_debtor_folder = None
        self.current_file = None
        self.in_debtor_folder = False
        self.preview_callback = None
        self.view_change_callback = None

    def set_preview_callback(self, callback):
        self.preview_callback = callback

    def set_view_change_callback(self, callback):
        self.view_change_callback = callback

    def load_file_preview(self, file_path):
        if self.preview_callback:
            self.preview_callback(file_path)

    def update_view(self):
        if self.view_change_callback:
            if (
                self.in_debtor_folder
                and self.current_company_id
                and self.current_debtor_folder
            ):
                self.view_change_callback(
                    "debtor", self.current_company_id, self.current_debtor_folder
                )
            elif self.current_company_id:
                self.view_change_callback("client", self.current_company_id)
            else:
                self.view_change_callback("bucket")


class ChatViewer:
    def __init__(self, shared_state):
        self.menu_items = []
        self.is_expanded = True
        self.current_path = ""
        self.files = []
        self.s3 = S3Middleware()
        self.bucket = config.aws_s3_tenant_storage_bucket
        self.file_list = None
        self.items = []
        self.root_level = True
        self.shared_state = shared_state
        self.selected_items = set()
        self._action_bar = None
        self.rename_dialog = None

    def handle_add_folder(self, folder_name):
        """Create a new folder in the current path"""
        new_folder_path = f"{self.current_path}{folder_name}/"
        print(f"Creating new folder: {new_folder_path}")

        # Create an empty file to represent the folder
        self.s3.put_object(self.bucket, new_folder_path + ".keep", "")

        # If we're at root level, create the required subfolders
        if self.root_level:
            print("Creating standard subfolders for client directory")
            # Create protected folder
            self.s3.put_object(self.bucket, new_folder_path + "protected/.keep", "")
            # Create public folder
            self.s3.put_object(self.bucket, new_folder_path + "public/.keep", "")
            # Create private folder
            self.s3.put_object(self.bucket, new_folder_path + "private/.keep", "")

        # Refresh the file list
        self.load_files()

    def show_add_folder_dialog(self):
        with ui.dialog() as dialog, ui.card():
            ui.label("Create New Folder").classes("text-xl font-bold mb-4")
            folder_name = ui.input("Folder name").classes("w-full")

            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Cancel", on_click=dialog.close).props("flat")
                ui.button(
                    "Create",
                    on_click=lambda: [
                        self.handle_add_folder(folder_name.value),
                        dialog.close(),
                    ],
                ).props("flat").classes("text-primary")
        dialog.open()

    def handle_rename_submit(self, old_path, new_name):
        print(f"Renaming {old_path} to {new_name}")

        # Determine if it's a folder or file
        is_folder = old_path.endswith("/") or "/" not in old_path
        old_name = old_path.rstrip("/")

        # Create new path
        if self.root_level:
            # At root level, just use the new name
            old_path = old_name  # Remove trailing slash for replacement
            new_path = new_name
        else:
            # In subfolders, maintain the path structure
            parent_path = "/".join(old_path.rstrip("/").split("/")[:-1])
            old_path = old_path.rstrip("/")  # Remove trailing slash for replacement
            new_path = f"{parent_path}/{new_name}"

        print(f"New path will be: {new_path}")

        if is_folder:
            # Handle folder renaming
            # Get all objects recursively using list_files to get full paths
            all_files = self.s3.list_files(self.bucket, old_path, clean_prefixes=False)
            print(f"Found {len(all_files)} files to copy")

            # If at root level, create standard folders first
            if self.root_level:
                # Create standard subfolders
                for subfolder in ["protected", "public", "private"]:
                    subfolder_path = f"{new_path}/{subfolder}/"
                    print(f"Creating subfolder: {subfolder_path}")
                    self.s3.put_object(self.bucket, subfolder_path + ".keep", "")

            # Move each file to new location
            for file_path in all_files:
                if file_path != old_path and not file_path.endswith(
                    "/.keep"
                ):  # Skip folder markers
                    new_file_path = file_path.replace(
                        old_path, new_path, 1
                    )  # Only replace first occurrence
                    print(f"Moving {file_path} to {new_file_path}")
                    success = self.s3.move_object(self.bucket, file_path, new_file_path)
                    if not success:
                        print(f"Failed to move file: {file_path}")
        else:
            # Handle single file renaming
            # Get the file content
            content = self.s3.get_file_content(self.bucket, old_path)
            if content:
                # Create new file with the new name
                print(f"Creating new file: {new_path}")
                success = self.s3.put_object(self.bucket, new_path, content)
                if success:
                    # Delete the old file
                    print(f"Deleting old file: {old_path}")
                    self.s3.delete_object(self.bucket, old_path)
                else:
                    print(f"Failed to create new file: {new_path}")

        # Refresh the file list
        self.load_files()

        # Clear selection
        self.selected_items.clear()
        self.render_action_bar.refresh()

    def show_rename_dialog(self, item):
        # Get just the filename/foldername without the path
        name = item.rstrip("/").split("/")[-1]
        # Determine if it's a file or folder
        is_folder = item.endswith("/") or "/" not in item

        with ui.dialog() as dialog, ui.card():
            if is_folder:
                ui.label("Rename Folder").classes("text-xl font-bold mb-4")
            else:
                ui.label("Rename File").classes("text-xl font-bold mb-4")
                # For files, get the extension to preserve it
                name_parts = name.rsplit(".", 1)
                base_name = name_parts[0]
                extension = name_parts[1] if len(name_parts) > 1 else ""

                # Only allow editing the base name, keep the extension
                new_name = ui.input("New name", value=base_name).classes("w-full")
                ui.label(f".{extension}").classes("text-gray-500")

                with ui.row().classes("w-full justify-end gap-2 mt-4"):
                    ui.button("Cancel", on_click=dialog.close).props("flat")
                    ui.button(
                        "Rename",
                        on_click=lambda: [
                            self.handle_rename_submit(
                                item, f"{new_name.value}.{extension}"
                            ),
                            dialog.close(),
                        ],
                    ).props("flat").classes("text-primary")
                dialog.open()
                return

            # For folders, allow editing the entire name
            new_name = ui.input("New name", value=name).classes("w-full")

            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Cancel", on_click=dialog.close).props("flat")
                ui.button(
                    "Rename",
                    on_click=lambda: [
                        self.handle_rename_submit(item, new_name.value),
                        dialog.close(),
                    ],
                ).props("flat").classes("text-primary")
        dialog.open()

    def handle_edit_click(self, item, e):
        print(f"Edit clicked for: {item}")  # Debug log

        # Clear any previous selection
        self.selected_items.clear()
        # Add the new selection
        self.selected_items.add(item)

        print(f"Selected items: {len(self.selected_items)}")  # Debug log
        self.show_rename_dialog(item)
        self.render_action_bar.refresh()

    @ui.refreshable
    def render_action_bar(self):
        print(
            f"Rendering action bar. Selected items: {len(self.selected_items)}"
        )  # Debug log
        with ui.row().classes("w-full items-center justify-between"):
            # Left side - Explorer label
            with ui.row():
                ui.label("Explorer").classes("text-lg font-medium text-primary")

            # Right side - action buttons
            with ui.row().classes("gap-2"):
                ui.button(
                    "Add", icon="add", on_click=self.show_add_folder_dialog
                ).props("flat dense").classes("text-primary")

    def update_file_list(self):
        if not self.file_list:
            return

        # Clear existing content
        self.file_list.clear()

        # Add items
        with self.file_list:
            for item in self.items:
                if len(item) == 2:  # Directory or back button
                    name, is_dir = item
                    if name == "../":  # Back navigation
                        with ui.item(
                            on_click=lambda n=name, d=is_dir: self.handle_click((n, d))
                        ).classes("cursor-pointer"):
                            with ui.item_section().props("side"):
                                ui.icon("arrow_back").props("size=small").classes(
                                    "text-gray-600"
                                )
                            with ui.item_section():
                                ui.label("Back").classes("font-semibold text-gray-600")
                        ui.separator()
                    else:  # Regular directory
                        with ui.item():
                            with ui.item_section().props("side"):
                                ui.button(
                                    icon="edit",
                                    on_click=lambda e, n=name: self.handle_edit_click(
                                        n, e
                                    ),
                                ).props("flat dense").classes(
                                    "text-primary"
                                    if name in self.selected_items
                                    else ""
                                )
                            with ui.item_section().props("side"):
                                ui.icon("folder").props("size=small").classes(
                                    "text-yellow-600"
                                )
                            with ui.item_section():
                                ui.label(name).classes("font-semibold")
                            with ui.item_section().props("top side"):
                                ui.button(
                                    "view",
                                    icon="chevron_right",
                                    on_click=lambda n=name, d=is_dir: self.handle_click(
                                        (n, d)
                                    ),
                                ).props("flat dense").classes("text-primary")
                        ui.separator()
                else:  # File with metadata
                    name, _, metadata, file_path = item
                    if self.shared_state.in_debtor_folder:
                        # In debtor folder, make items clickable for preview
                        with ui.item():
                            with ui.item_section().props("side"):
                                ui.button(
                                    icon="edit",
                                    on_click=lambda e, f=file_path: self.handle_edit_click(
                                        f, e
                                    ),
                                ).props("flat dense").classes(
                                    "text-primary"
                                    if file_path in self.selected_items
                                    else ""
                                )
                            with ui.item_section().props("side"):
                                ui.icon("description").props("size=small").classes(
                                    "text-green-600"
                                )
                            with ui.item_section():
                                ui.item_label(name).classes("text-gray-800")
                                ui.item_label(
                                    f"Size: {metadata.get('Size', 'Unknown')}, Modified: {metadata.get('LastModified', 'Unknown')}"
                                ).classes("text-sm text-gray-500").props("caption")
                            with ui.item_section().props("top side"):
                                ui.button(
                                    "view",
                                    icon="chevron_right",
                                    on_click=lambda f=file_path: self.handle_file_click(
                                        f
                                    ),
                                ).props("flat dense").classes("text-primary")
                                ui.button(
                                    icon="download",
                                    on_click=lambda f=file_path: self.download_file(f),
                                ).props("flat dense round").classes("text-primary")
                    else:
                        # Outside debtor folder, show only download button
                        with ui.item():
                            with ui.item_section().props("side"):
                                ui.button(
                                    icon="edit",
                                    on_click=lambda e, f=file_path: self.handle_edit_click(
                                        f, e
                                    ),
                                ).props("flat dense").classes(
                                    "text-primary"
                                    if file_path in self.selected_items
                                    else ""
                                )
                            with ui.item_section().props("side"):
                                ui.icon("description").props("size=small").classes(
                                    "text-green-600"
                                )
                            with ui.item_section():
                                ui.item_label(name).classes("text-gray-800")
                                ui.item_label(
                                    f"Size: {metadata.get('Size', 'Unknown')}, Modified: {metadata.get('LastModified', 'Unknown')}"
                                ).classes("text-sm text-gray-500").props("caption")
                            with ui.item_section().props("top side"):
                                ui.button(
                                    icon="download",
                                    on_click=lambda f=file_path: self.download_file(f),
                                ).props("flat dense round").classes("text-primary")
                        ui.separator()

    def handle_file_click(self, file_path):
        """Handle file click in debtor folder"""
        if self.shared_state.in_debtor_folder:
            self.shared_state.load_file_preview(file_path)

    def load_files(self):
        self.items = []
        response = self.s3.list_objects(self.bucket, self.current_path)

        # Update root_level based on current path
        self.root_level = self.current_path == ""

        if self.current_path:
            self.items.append(("../", True))

        # Add directories first
        if response and "directories" in response:
            for directory in response["directories"]:
                name = directory.rstrip("/").split("/")[-1]
                self.items.append((name, True))

        # Then add files
        if response and "files" in response:
            for file_path in response["files"]:
                name = file_path.split("/")[-1]
                if name:  # Skip empty names
                    metadata = self.s3.get_file_metadata(self.bucket, file_path)
                    self.items.append((name, False, metadata, file_path))

        self.update_file_list()

    def handle_click(self, item):
        name, is_dir = item
        if name == "../":
            # If we're in a protected folder, go back to root
            if "/protected" in self.current_path:
                self.current_path = ""
                self.shared_state.current_company_id = None
                self.shared_state.in_debtor_folder = False
                self.shared_state.current_debtor_folder = None
                self.shared_state.update_view()
            else:
                path_parts = [p for p in self.current_path.split("/") if p]
                if path_parts:
                    path_parts.pop()
                self.current_path = "/".join(path_parts)
                if self.current_path:
                    self.current_path += "/"
                    # If we're back at the client level, show client details
                    if len(path_parts) == 1:
                        self.shared_state.in_debtor_folder = False
                        self.shared_state.current_company_id = path_parts[0]
                        self.shared_state.current_debtor_folder = None
                        self.shared_state.update_view()
                else:
                    self.shared_state.current_company_id = None
                    self.shared_state.in_debtor_folder = False
                    self.shared_state.current_debtor_folder = None
                    self.shared_state.update_view()
        elif is_dir:
            if self.root_level:
                # If clicking a client folder at root level
                print(f"Showing client details for: {name}")  # Debug log
                self.shared_state.current_company_id = name
                self.shared_state.in_debtor_folder = False
                self.shared_state.current_debtor_folder = None
                self.current_path = f"{name}/protected/"
                self.shared_state.update_view()
            else:
                # If we're in a client's protected folder
                if (
                    self.shared_state.current_company_id
                    and "protected" in self.current_path
                ):
                    print(
                        f"Showing debtor details for: {self.shared_state.current_company_id}/{name}"
                    )
                    self.shared_state.in_debtor_folder = True
                    self.shared_state.current_debtor_folder = name
                    self.shared_state.update_view()
                self.current_path += f"{name}/"

        self.load_files()

    def render(self):
        with ui.column().classes("w-full h-full p-4"):
            with ui.card().classes("w-full h-full rounded-lg overflow-hidden"):
                # Fixed header
                with ui.column().classes("w-full p-4"):
                    # Action bar
                    with ui.card().classes("w-full p-2 rounded-lg").style(
                        """
                        background-color: #FFFFFF;
                        border: 1px solid rgba(88,152,212,0.3);
                        box-shadow: 0 0 0 1px rgba(88,152,212,0.2);
                        """
                    ):
                        self._action_bar = self.render_action_bar()

                # Scrollable content
                with ui.scroll_area().classes("w-full flex-grow"):
                    self.file_list = (
                        ui.list().props("bordered separator").classes("w-full")
                    )
                    ui.timer(0.1, lambda: self.load_files(), once=True)

    def download_file(self, file_path):
        """Download the file using a presigned URL"""
        url = self.s3.generate_presigned_url(self.bucket, file_path)
        if url:
            filename = file_path.split("/")[-1]
            ui.download(url, filename=filename)


class BucketDetails:
    def __init__(self, s3, bucket):
        self.s3 = s3
        self.bucket = bucket

    def render(self):
        with ui.scroll_area().classes("w-full h-full"):
            with ui.list().props("bordered separator").classes("w-full"):
                ui.item_label("Recent Uploads").props("header").classes(
                    "text-bold text-lg"
                )
                ui.separator()
                recent_uploads = self.s3.get_recent_uploads(self.bucket)
                print(f"Recent uploads found: {len(recent_uploads)}")
                if not recent_uploads:
                    ui.label("No recent uploads found").classes("text-gray-500 p-4")
                for file_path, last_modified in recent_uploads:
                    print(f"Processing file: {file_path}")
                    with ui.item():
                        with ui.item_section().props("side"):
                            ui.icon("description").props("size=small").classes(
                                "text-green-600"
                            )
                        with ui.item_section():
                            ui.item_label(file_path.split("/")[-1]).classes(
                                "text-gray-800"
                            )
                            ui.item_label(
                                f"Modified: {last_modified.strftime('%Y-%m-%d %H:%M:%S')}"
                            ).classes("text-sm text-gray-500").props("caption")
                        with ui.item_section().props("top side"):
                            ui.button(
                                icon="download",
                                on_click=lambda f=file_path: self.download_file(f),
                            ).props("flat dense round").classes("text-primary")
                    ui.separator()

    def download_file(self, file_path):
        url = self.s3.generate_presigned_url(self.bucket, file_path)
        if url:
            ui.download(url, filename=file_path.split("/")[-1])


class ClientDetails:
    def __init__(self, s3, bucket, dynamo, company_id):
        self.s3 = s3
        self.bucket = bucket
        self.dynamo = dynamo
        self.company_id = company_id
        self.client_data = None
        self.list_manager = ListManager()
        self.load_client_data()

    def get_client_name(self):
        if not self.company_id.startswith("CL_"):
            return "Unknown Company"

        client_number = self.company_id.split("CL_")[1]
        client_map = self.list_manager.get_list("client_map")
        return client_map.get(client_number, "Unknown Company")

    def load_client_data(self):
        key = {"company_id": {"S": self.company_id}}
        self.client_data = self.dynamo.get_item(key)

    def get_client_recent_uploads(self):
        recent_uploads = self.s3.get_recent_uploads(self.bucket)
        # Filter for only this client's files
        client_uploads = [
            (path, modified)
            for path, modified in recent_uploads
            if path.startswith(f"{self.company_id}/")
        ]
        return client_uploads

    def render(self):
        with ui.column().classes("w-full h-full"):
            if not self.client_data:
                ui.label(f"No data found for client {self.company_id}").classes(
                    "text-red-500 p-4"
                )
                return

            # Fixed header section
            with ui.column().classes("w-full p-4"):
                # Client header
                with ui.row().classes("w-full items-center justify-between"):
                    ui.label(self.get_client_name()).classes("text-2xl font-bold")
                    ui.label(f"ID: {self.company_id}").classes("text-gray-500")

                ui.separator()

                # Client details
                with ui.column().classes("w-full gap-2"):
                    if "email" in self.client_data:
                        ui.label(f"Email: {self.client_data['email']['S']}").classes(
                            "text-gray-700"
                        )
                    if "phone" in self.client_data:
                        ui.label(f"Phone: {self.client_data['phone']['S']}").classes(
                            "text-gray-700"
                        )
                    if "address" in self.client_data:
                        ui.label(
                            f"Address: {self.client_data['address']['S']}"
                        ).classes("text-gray-700")

                ui.separator()
                ui.label("Recent Uploads").classes("text-xl font-bold")

            # Scrollable recent uploads section
            with ui.scroll_area().classes("w-full flex-grow"):
                recent_uploads = self.get_client_recent_uploads()

                if recent_uploads:
                    with ui.list().props("bordered separator").classes("w-full"):
                        for file_path, last_modified in recent_uploads:
                            with ui.item():
                                with ui.item_section().props("side"):
                                    ui.icon("description").props("size=small").classes(
                                        "text-green-600"
                                    )
                                with ui.item_section():
                                    ui.item_label(file_path.split("/")[-1]).classes(
                                        "text-gray-800"
                                    )
                                    ui.item_label(
                                        f"Modified: {last_modified.strftime('%Y-%m-%d %H:%M:%S')}"
                                    ).classes("text-sm text-gray-500").props("caption")
                                with ui.item_section().props("top side"):
                                    ui.button(
                                        icon="download",
                                        on_click=lambda f=file_path: self.download_file(
                                            f
                                        ),
                                    ).props("flat dense round").classes("text-primary")
                else:
                    ui.label("No recent uploads found").classes("text-gray-500 p-4")

    def preview_file(self, file_path):
        content = self.s3.get_file_content_base64(self.bucket, file_path)
        if content:
            mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
            ui.open(f"data:{mime_type};base64,{content}")

    def download_file(self, file_path):
        url = self.s3.generate_presigned_url(self.bucket, file_path)
        if url:
            ui.download(url, filename=file_path.split("/")[-1])


class DebtorDetails:
    def __init__(self, s3, bucket, dynamo, company_id, debtor_folder):
        self.s3 = S3Middleware()
        self.bucket = bucket
        self.dynamo = dynamo
        self.company_id = company_id
        self.debtor_folder = debtor_folder
        self.client_data = None
        self.list_manager = ListManager()
        self.current_file = None
        self.file_preview = None
        self.file_type = None
        self.preview_container = None
        self.action_bar = None
        self.load_client_data()

    def get_client_name(self):
        if not self.company_id.startswith("CL_"):
            return "Unknown Company"

        client_number = self.company_id.split("CL_")[1]
        client_map = self.list_manager.get_list("client_map")
        return client_map.get(client_number, "Unknown Company")

    def load_client_data(self):
        key = {"company_id": {"S": self.company_id}}
        self.client_data = self.dynamo.get_item(key)

    def load_file_preview(self, file_path):
        print(f"Loading file preview for: {file_path}")  # Debug log
        content = self.s3.get_file_content(self.bucket, file_path)
        if content:
            self.current_file = file_path
            mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
            print(f"File type detected: {mime_type}")  # Debug log

            if mime_type == "application/pdf":
                self.file_preview = content
                self.file_type = "pdf"
            elif mime_type == "text/csv":
                try:
                    csv_content = content.decode("utf-8")
                    self.file_preview = pd.read_csv(StringIO(csv_content))
                    self.file_type = "spreadsheet"
                except Exception as e:
                    print(f"Error parsing CSV: {e}")  # Debug log
                    self.file_type = "unsupported"
            elif mime_type in [
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ]:
                try:
                    from io import BytesIO

                    excel_content = BytesIO(content)
                    self.file_preview = pd.read_excel(excel_content)
                    self.file_type = "spreadsheet"
                except Exception as e:
                    print(f"Error parsing Excel: {e}")  # Debug log
                    self.file_type = "unsupported"
            else:
                self.file_type = "unsupported"

            print(f"Preview loaded, type: {self.file_type}")  # Debug log

            # Update the preview
            if self.preview_container:
                self.preview_container.clear()
                with self.preview_container:
                    self.render_preview()

            # Update the action bar
            if self.action_bar:
                print("Refreshing action bar")  # Debug log
                self.action_bar.refresh()

    def download_file(self, file_path):
        """Download the current file using a presigned URL"""
        print(f"Downloading file: {file_path}")  # Debug log
        url = self.s3.generate_presigned_url(self.bucket, file_path)
        if url:
            filename = file_path.split("/")[-1]
            ui.download(url, filename=filename)

    @ui.refreshable
    def render_action_bar(self):
        print(f"Rendering action bar, current file: {self.current_file}")  # Debug log
        with ui.row().classes("w-full items-center justify-between"):
            # Left side - Document label
            with ui.row():
                ui.label("Document").classes("text-lg font-medium text-primary")

            # Right side - download button
            with ui.row().classes("gap-2"):
                if self.current_file:
                    ui.button(
                        icon="download",
                        on_click=lambda: self.download_file(self.current_file),
                    ).props("flat dense round").classes("text-primary")

    def render_preview(self):
        if self.current_file:
            if self.file_type == "pdf":
                self.render_pdf_preview()
            elif self.file_type == "spreadsheet":
                self.render_spreadsheet_preview()
            else:
                self.render_unsupported_file_type()
        else:
            with ui.column().classes("w-full h-full items-center justify-center"):
                ui.label("Select a document to view").classes("text-gray-500")

    def render_spreadsheet_preview(self):
        """Renders spreadsheet preview (CSV, XLS, XLSX) using AgGrid"""
        if self.file_preview is not None:
            data = self.file_preview.to_dict(orient="records")
            columns = [
                {"headerName": col, "field": col, "hide": False}
                for col in self.file_preview.columns
            ]

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
                    f"Error loading PDF preview for file: {self.current_file}"
                ).classes("text-red-500")
                ui.label("Please check the server logs for more information.").classes(
                    "text-red-500"
                )

    def render_unsupported_file_type(self):
        with ui.column().style(
            "width: 100%; height: 100%; justify-content: center; align-items: center;"
        ):
            ui.label(
                "Unsupported file type. Please download the file to view its contents."
            ).classes("text-lg text-bold")

    def render(self):
        with ui.column().classes("w-full h-full"):
            if not self.client_data:
                ui.label(f"No data found for client {self.company_id}").classes(
                    "text-red-500 p-4"
                )
                return

            # Fixed header section
            with ui.column().classes("w-full p-4"):
                # Client header with debtor subtext
                with ui.column().classes("w-full gap-1"):
                    with ui.row().classes("w-full items-center justify-between"):
                        ui.label(self.get_client_name()).classes("text-2xl font-bold")
                        ui.label(f"ID: {self.company_id}").classes("text-gray-500")
                    with ui.row().classes("items-center gap-2"):
                        ui.label("Debtor:").classes("text-gray-600")
                        ui.label(self.debtor_folder).classes("text-gray-800")

                ui.separator()

                # Action bar
                with ui.card().classes("w-full p-2 rounded-lg").style(
                    """
                    background-color: #FFFFFF;
                    border: 1px solid rgba(88,152,212,0.3);
                    box-shadow: 0 0 0 1px rgba(88,152,212,0.2);
                    """
                ):
                    self.action_bar = self.render_action_bar()

            # Preview area
            self.preview_container = ui.column().classes(
                "w-full flex-grow overflow-auto"
            )
            with self.preview_container:
                self.render_preview()

    def get_debtor_recent_uploads(self):
        recent_uploads = self.s3.get_recent_uploads(self.bucket)
        # Filter for only this debtor's files
        debtor_path = f"{self.company_id}/protected/{self.debtor_folder}"
        debtor_uploads = [
            (path, modified)
            for path, modified in recent_uploads
            if path.startswith(debtor_path)
        ]
        return debtor_uploads

    def preview_file(self, file_path):
        content = self.s3.get_file_content_base64(self.bucket, file_path)
        if content:
            mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
            ui.open(f"data:{mime_type};base64,{content}")

    def download_file(self, file_path):
        """Download the current file using a presigned URL"""
        url = self.s3.generate_presigned_url(self.bucket, file_path)
        if url:
            filename = file_path.split("/")[-1]
            ui.download(url, filename=filename)


class DocViewer:
    def __init__(self, dynamo_middleware, shared_state):
        self.s3 = S3Middleware()
        self.bucket = config.aws_s3_tenant_storage_bucket
        self.dynamo = dynamo_middleware
        self.current_view = None
        self.container = None
        self.shared_state = shared_state
        self.shared_state.set_preview_callback(self.load_file_preview)
        self.shared_state.set_view_change_callback(self.handle_view_change)
        self.show_bucket_details()

    def handle_view_change(self, view_type, *args):
        if view_type == "bucket":
            self.show_bucket_details()
        elif view_type == "client":
            self.show_client_details(args[0])
        elif view_type == "debtor":
            self.show_debtor_details(args[0], args[1])

    def load_file_preview(self, file_path):
        if self.current_view and hasattr(self.current_view, "load_file_preview"):
            self.current_view.load_file_preview(file_path)

    def show_bucket_details(self):
        print("Switching to BucketDetails view")  # Debug log
        self.current_view = BucketDetails(self.s3, self.bucket)
        self._refresh_view()

    def show_client_details(self, company_id):
        print(f"Switching to ClientDetails view for {company_id}")  # Debug log
        self.current_view = ClientDetails(self.s3, self.bucket, self.dynamo, company_id)
        self._refresh_view()

    def show_debtor_details(self, company_id, debtor_folder):
        print(
            f"Switching to DebtorDetails view for {company_id}/{debtor_folder}"
        )  # Debug log
        self.current_view = DebtorDetails(
            self.s3, self.bucket, self.dynamo, company_id, debtor_folder
        )
        self._refresh_view()

    def _refresh_view(self):
        if self.container:
            self.container.clear()
            with self.container:
                if self.current_view:
                    self.current_view.render()

    def render(self):
        with ui.column().classes("w-full h-full p-4"):
            self.container = ui.card().classes(
                "w-full h-full rounded-lg overflow-hidden"
            )
            with self.container:
                if self.current_view:
                    self.current_view.render()


class InteliDocPage(StandardPage):
    def __init__(self, session_manager):
        super().__init__(
            session_manager,
            page_config={
                "page_title": "InteliDoc",
                "page_icon": "intelidoc",
                "page_route": "/intelidoc",
                "page_root_route": "/",
                "page_description": "InteliDoc",
                "nav_position": "top",
            },
        )
        self.tenant_s3 = config.aws_s3_tenant_storage_bucket
        self.dynamo_middleware = DynamoMiddleware(config.aws_companies_table_name)
        self.s3_middleware = S3Middleware()
        self.shared_state = SharedState()
        self._on_page_load()

    def _on_page_load(self):
        self.doc_viewer = DocViewer(self.dynamo_middleware, self.shared_state)
        self.chat_viewer = ChatViewer(self.shared_state)

    def page_content(self):
        with ui.grid(columns=5).classes("w-full h-[89vh] gap-0"):
            chat_column = ui.column().classes("col-span-2 justify-center items-center")
            with chat_column:
                self.chat_viewer.render()

            doc_column = ui.column().classes("col-span-3 justify-center items-center")
            with doc_column:
                self.doc_viewer.render()


def intelidoc_page(session_manager):
    page = InteliDocPage(session_manager)
    page.render()
