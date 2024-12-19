from nicegui import ui
from middleware.cognito import CognitoMiddleware
from middleware.s3 import S3Middleware
from middleware.dynamo import DynamoMiddleware
import os
from modules import TokenManager, TokenType
from PIL import Image
from io import BytesIO
from config import config
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime


class UserProfile(BaseModel):
    user_id: str
    company_id: str
    role: str
    responsibilities: List[Dict]
    updated_on: datetime
    updated_by: str
    created_on: datetime
    created_by: str
    goals: List[Dict]

    class Config:
        json_encoders = {
            datetime: lambda dt: int(
                dt.timestamp()
            )  # Convert to Unix timestamp for DynamoDB
        }


class UserSettingsComponent:
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.cognito_middleware = CognitoMiddleware()
        self.s3_middleware = S3Middleware()
        self.users_dynamo_middleware = DynamoMiddleware(config.aws_users_table_name)
        self.user_id = None
        self.company_id = None
        self.avatar_key = None
        self.user = None
        self.user_profile = None
        self._get_user()

    def _get_user(self):
        token = self.session_manager.get("id_token")
        token_manager = TokenManager(TokenType.ID, token)
        user = token_manager.get_decoded_token().dict()

        self.user_id = user.get("sub")
        self.company_id = self.cognito_middleware.get_all_custom_attributes(
            self.session_manager.get("username")
        ).get("custom:company_id")
        self.avatar_key = f"{self.company_id}/users/{self.user_id}/public/images/avatar"
        self.user = user

        # Get or create user profile
        self.user_profile = self.get_user_profile()

    def handle_avatar_upload(self, e):
        try:
            file = e.content
            # Resize image to standard size
            img = Image.open(BytesIO(file))
            img = img.resize((200, 200))

            # Convert to bytes
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            # Upload to S3
            self.s3_middleware.upload_fileobj(
                buffer, self.avatar_key + ".png", ExtraArgs={"ContentType": "image/png"}
            )

            # Refresh avatar display
            self.avatar_img.source = self.get_avatar_url()

        except Exception as e:
            ui.notify(f"Error uploading avatar: {str(e)}", type="error")

    def get_avatar_url(self):
        try:
            url = self.s3_middleware.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.s3_middleware.bucket_name,
                    "Key": self.avatar_key + ".png",
                },
                ExpiresIn=3600,
            )
            return url
        except:
            return "https://cdn-icons-png.flaticon.com/512/1077/1077114.png"

    def get_user_profile(self):
        try:
            # Try to get existing record
            key = {"user_id": {"S": self.user_id}, "company_id": {"S": self.company_id}}

            user_record = self.users_dynamo_middleware.get_item(key)

            if not user_record:
                # Create new profile if none exists
                new_profile = UserProfile(
                    user_id=self.user_id,
                    company_id=self.company_id,
                    role="",  # Default empty role
                    responsibilities=[],  # Empty responsibilities list
                    updated_on=datetime.now(),
                    updated_by=self.user_id,
                    created_on=datetime.now(),
                    created_by=self.user_id,
                    goals=[],  # Empty goals list
                )

                # Convert to DynamoDB format
                profile_item = {
                    "user_id": {"S": new_profile.user_id},
                    "company_id": {"S": new_profile.company_id},
                    "role": {"S": new_profile.role},
                    "responsibilities": {"L": []},
                    "updated_on": {"N": str(int(new_profile.updated_on.timestamp()))},
                    "updated_by": {"S": new_profile.updated_by},
                    "created_on": {"N": str(int(new_profile.created_on.timestamp()))},
                    "created_by": {"S": new_profile.created_by},
                    "goals": {"L": []},
                }

                # Save to DynamoDB
                self.users_dynamo_middleware.put_item(profile_item)
                return new_profile

            # Convert DynamoDB record to UserProfile
            return UserProfile(
                user_id=user_record["user_id"]["S"],
                company_id=user_record["company_id"]["S"],
                role=user_record["role"]["S"],
                responsibilities=[
                    dict(r["M"]) for r in user_record["responsibilities"]["L"]
                ],
                updated_on=datetime.fromtimestamp(int(user_record["updated_on"]["N"])),
                updated_by=user_record["updated_by"]["S"],
                created_on=datetime.fromtimestamp(int(user_record["created_on"]["N"])),
                created_by=user_record["created_by"]["S"],
                goals=[dict(g["M"]) for g in user_record["goals"]["L"]],
            )

        except Exception as e:
            print(f"Error getting user profile: {str(e)}")
            return None

    def render(self):
        avatar_url = self.get_avatar_url()

        with ui.grid(rows=3).classes("w-full h-full gap-2"):
            with ui.row().classes("row-span-2 w-full"):
                with ui.grid(columns=4).classes("w-full h-full"):
                    with ui.column().classes("col-span-1"):
                        with ui.card().classes("w-full h-full rounded-lg flex-col"):
                            with ui.grid(rows=3).classes("w-full h-full"):
                                with ui.row().classes(
                                    "row-span-1 items-center justify-center"
                                ):
                                    with ui.avatar().classes("w-36 h-36"):
                                        ui.image(avatar_url).classes(
                                            "object-cover rounded-full h-[90%] w-[90%]"
                                        )
                                with ui.row().classes("row-span-2 w-full h-full"):
                                    with ui.column().classes(
                                        "w-full h-full pt-4 gap-0"
                                    ):
                                        with ui.row().classes(
                                            "w-full items-center justify-center"
                                        ):
                                            ui.label(f"{self.user.get('name')}").style(
                                                "font-size: 1.5rem; font-weight: bold;"
                                            )
                                        with ui.row().classes(
                                            "w-full items-center justify-center"
                                        ):
                                            ui.label(f"{self.user_profile.role}").style(
                                                "font-size: 1.2rem; font-weight: 500; color: #666;"
                                            )
                                        with ui.column().classes(
                                            "w-full flex-grow items-center justify-center"
                                        ):
                                            with ui.row().classes(
                                                "w-full items-center justify-center"
                                            ):
                                                ui.button(
                                                    icon="key", text="Reset Password"
                                                ).classes("w-2/3 rounded-lg").props(
                                                    "outline"
                                                )
                                            with ui.row().classes(
                                                "w-full items-center justify-center"
                                            ):
                                                ui.button(
                                                    icon="camera_alt",
                                                    text="Change Photo",
                                                ).classes("w-2/3 rounded-lg").props(
                                                    "outline"
                                                )

                    with ui.column().classes("col-span-3 p-6"):
                        with ui.grid(columns=3).classes("w-full h-full"):
                            with ui.column().classes("col-span-1 w-full"):
                                ui.input(
                                    label="First Name",
                                    value=self.user.get("given_name"),
                                ).classes("w-full   ").props("outlined")
                                ui.input(
                                    label="Last Name",
                                    value=self.user.get("family_name"),
                                ).classes("w-full").props("outlined")
                                ui.input(
                                    label="Email",
                                    value=self.user.get("email"),
                                ).classes("w-full").props("outlined")
                                ui.input(
                                    label="Phone",
                                    value=self.user.get("phone_number"),
                                ).classes("w-full").props("outlined")
                            with ui.column().classes("col-span-2 w-full"):
                                pass

            with ui.row().classes("row-span-1 w-full").style(
                "border-top: 1px solid #e0e0e0; max-height: 40vh;"
            ):
                with ui.grid(columns=2).classes("w-full h-full gap-2"):
                    with ui.column().classes("flex-grow"):
                        with ui.card().classes("w-full h-[28vh] rounded-lg"):
                            with ui.column().classes("w-full h-full gap-0"):
                                ui.label("Goals").style(
                                    "font-size: 1.2rem; font-weight: bold; padding: 0.5rem;"
                                )
                                with ui.scroll_area().classes("w-full").style(
                                    "max-height: 30vh;"
                                ):
                                    with ui.list().props("bordered separator").classes(
                                        "w-full"
                                    ):
                                        if (
                                            self.user_profile
                                            and self.user_profile.goals
                                        ):
                                            for goal in self.user_profile.goals:
                                                with ui.item().classes("w-full"):
                                                    with ui.row().classes(
                                                        "w-full justify-between items-center"
                                                    ):
                                                        with ui.column().classes(
                                                            "flex-grow"
                                                        ):
                                                            ui.label(
                                                                goal.get(
                                                                    "goal_name", {}
                                                                ).get("S", "")
                                                            ).style("font-weight: 500;")
                                                            ui.label(
                                                                goal.get(
                                                                    "goal_description",
                                                                    {},
                                                                ).get("S", "")
                                                            ).style(
                                                                "font-size: 0.9rem; color: #666;"
                                                            )
                                                        with ui.column().classes(
                                                            "flex-shrink-0"
                                                        ):
                                                            priority = goal.get(
                                                                "goal_priority", {}
                                                            ).get("N", "1")
                                                            status = goal.get(
                                                                "goal_status", {}
                                                            ).get("S", "pending")
                                                            ui.badge(
                                                                str(priority),
                                                                color={
                                                                    "1": "green",
                                                                    "2": "orange",
                                                                    "3": "red",
                                                                }.get(priority, "grey"),
                                                            ).classes("q-mr-sm")
                                                            ui.badge(
                                                                status,
                                                                color={
                                                                    "pending": "grey",
                                                                    "in_progress": "blue",
                                                                    "completed": "green",
                                                                }.get(status, "grey"),
                                                            )
                                        else:
                                            with ui.row().classes(
                                                "w-full justify-center items-center p-4"
                                            ):
                                                ui.label("No goals found").style(
                                                    "color: #666;"
                                                )

                    with ui.column().classes("flex-grow"):
                        with ui.card().classes("w-full h-[28vh] rounded-lg"):
                            ui.label("Roles & Responsibilities")
