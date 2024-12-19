import boto3
import uuid
from nicegui import app, ui
from botocore.exceptions import ClientError
from datetime import datetime, timezone, timedelta

from modules import PermissionManager, TokenManager, TokenType
from config import config


class CognitoMiddleware:
    def __init__(self):
        self.user_pool_id = config.aws_cognito_user_pool_id
        self.client_id = config.aws_cognito_client_id
        self.region = config.aws_region
        self.client = boto3.client("cognito-idp", region_name=config.aws_region)
        self.dynamodb_client = None
        self.dynamodb_table = None
        self.user_permissions = []
        self.isAuthenticated = False
        self.user_uuid = None
        self.permission_manager = PermissionManager()
        self._onload()

    def _onload(self):
        self.dynamodb_client = boto3.resource("dynamodb", region_name=self.region)
        self.dynamodb_table = self.dynamodb_client.Table(config.aws_sessions_table_name)

    def initialize_user(self):
        """Initialize user context within a page builder function."""
        if not self.is_authenticated():
            username = app.storage.user.get("username")
            session_id = app.storage.user.get("session_id")
            if username and session_id:
                # Verify session validity
                if self.verify_session(username, session_id):
                    self.isAuthenticated = True
                    self.user_id = self.get_user_id()
                    self.get_user_groups(app.storage.user.get("access_token"))
                else:
                    self.signout()
                    print("Invalid or expired session.")
            else:
                print("No user or session found in storage.")
        else:
            print("User already authenticated.")

    def is_authenticated(self):
        """Check if the user is authenticated."""
        return (
            app.storage.user.get("username") is not None
            and app.storage.user.get("session_id") is not None
            and app.storage.user.get("access_token") is not None
        )

    def signin(self, username, password):
        try:
            response = self.client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={"USERNAME": username, "PASSWORD": password},
            )
            challenge_name = response.get("ChallengeName")

            if challenge_name == "SMS_MFA":
                app.storage.user["challenge"] = challenge_name
                app.storage.user["session"] = response.get("Session")
                app.storage.user["username"] = username
                return "SMS_MFA"
            elif challenge_name == "NEW_PASSWORD_REQUIRED":
                app.storage.user["challenge"] = challenge_name
                app.storage.user["session"] = response.get("Session")
                app.storage.user["username"] = username
                return "NEW_PASSWORD_REQUIRED"
            elif challenge_name == "MFA_SETUP_REQUIRED":
                app.storage.user["challenge"] = challenge_name
                app.storage.user["session"] = response.get("Session")
                app.storage.user["username"] = username
                return "MFA_SETUP_REQUIRED"
            else:
                authentication_result = response.get("AuthenticationResult")
                print("authentication_result", authentication_result)
                app.storage.user["refresh_token"] = authentication_result.get(
                    "RefreshToken"
                )
                app.storage.user["access_token"] = authentication_result.get(
                    "AccessToken"
                )
                app.storage.user["id_token"] = authentication_result.get("IdToken")
                app.storage.user["username"] = username

                # Generate a unique session_id
                session_id = f"{uuid.uuid4()}"
                app.storage.user["session_id"] = session_id

                # Store session in DynamoDB
                expiration_time = datetime.now(timezone.utc) + timedelta(
                    hours=1
                )  # Example: 1-hour session
                self.store_session(
                    username,
                    session_id,
                    expiration_time,
                    authentication_result.get("AccessToken"),
                )

                self.get_user_groups(app.storage.user.get("access_token"))
                self.isAuthenticated = True
                self.user_id = self.get_user_id()
                return authentication_result
        except ClientError as e:
            print("signin function error", e)
            return None

    def signout(self):
        """Sign out the user and clear the session."""
        print("Signing out user...")
        try:
            self.client.global_sign_out(
                AccessToken=app.storage.user.get("access_token")
            )
        except ClientError as e:
            print(f"Error during global sign-out: {e}")
        self.invalidate_session(
            app.storage.user.get("username"), app.storage.user.get("session_id")
        )
        self.isAuthenticated = False
        app.storage.user.clear()
        ui.navigate.to("/signin")

    def handle_mfa(self, mfa_code):
        try:
            session = app.storage.user.get("session")
            username = app.storage.user.get("username")

            if not username or not session:
                raise ValueError("Session or username not found in storage.")

            response = self.client.respond_to_auth_challenge(
                ClientId=self.client_id,
                ChallengeName="SMS_MFA",
                Session=session,
                ChallengeResponses={"USERNAME": username, "SMS_MFA_CODE": mfa_code},
            )
            authentication_result = response.get("AuthenticationResult")
            if authentication_result:
                # Generate a unique session_id
                session_id = str(uuid.uuid4())
                app.storage.user["session_id"] = session_id

                # Store session in DynamoDB
                expiration_time = datetime.now(timezone.utc) + timedelta(
                    hours=1
                )  # Example: 1-hour session
                self.store_session(
                    username,
                    session_id,
                    expiration_time,
                    authentication_result.get("AccessToken"),
                )

                self.store_tokens(
                    authentication_result.get("AccessToken"),
                    authentication_result.get("IdToken"),
                    authentication_result.get("RefreshToken"),
                    expiration_time,
                )
                self.get_user_groups(authentication_result.get("AccessToken"))
                # self.get_user_groups(authentication_result.get("Username"))
                self.isAuthenticated = True
                self.user_id = (
                    self.get_user_id()
                )  # authentication_result.get("Username")
                return authentication_result
        except ClientError as e:
            print(f"MFA handling error: {e}")
            return None

    def handle_new_password(self, new_password, confirm_password):
        try:
            if new_password != confirm_password:
                raise ValueError("Passwords do not match.")

            session = app.storage.user.get("session")
            username = app.storage.user.get("username")

            if not username or not session:
                raise ValueError("Session or username not found in storage.")

            response = self.client.respond_to_auth_challenge(
                ClientId=self.client_id,
                ChallengeName="NEW_PASSWORD_REQUIRED",
                Session=session,
                ChallengeResponses={
                    "USERNAME": username,
                    "NEW_PASSWORD": new_password,
                },
            )

            # Password reset complete, no need for MFA at this point
            authentication_result = response.get("AuthenticationResult")
            if authentication_result:
                # Generate a unique session_id
                session_id = str(uuid.uuid4())
                app.storage.user["session_id"] = session_id

                # Store session in DynamoDB
                expiration_time = datetime.now(timezone.utc) + timedelta(
                    hours=1
                )  # Example: 1-hour session
                self.store_session(username, session_id, expiration_time)

                self.store_tokens(
                    authentication_result.get("AccessToken"),
                    authentication_result.get("IdToken"),
                    authentication_result.get("RefreshToken"),
                    expiration_time,
                )
                self.get_user_groups(authentication_result.get("AccessToken"))
                self.isAuthenticated = True
                self.user_id = self.get_user_id(
                    authentication_result.get("AccessToken")
                )
                return authentication_result
            else:
                # If no authentication result, MFA might be required; return specific flag if needed
                return None
        except ClientError as e:
            print(e)
            return None

    def has_permission(self, required_permissions):
        """
        Check if the user has the required permissions.

        Args:
            required_permissions (str or list): A single permission or a list of permissions.

        Returns:
            bool: True if the user has any of the required permissions, False otherwise.
        """
        if isinstance(required_permissions, str):
            required_permissions = [required_permissions]

        user_groups = app.storage.user.get("user_groups", [])

        # Check if any user group starts with '_role_'
        role_groups = [group for group in user_groups if group.startswith("_role_")]

        for role_group in role_groups:
            role = role_group
            if role in self.permission_manager.get_all_roles():
                role_permissions = self.permission_manager.get_permissions(
                    role=role, cleaned_list=False
                )
                if any(perm in role_permissions for perm in required_permissions):
                    return True

        # If not found in roles, check individual permissions
        return any(perm in user_groups for perm in required_permissions)

    def get_user_groups(self, provided_token=None):
        if provided_token is None:
            access_token = app.storage.user.get("access_token")
            token = TokenManager(
                token_type=TokenType.ACCESS, encoded_token=access_token
            )
            decoded_token = token.get_decoded_token()
        else:
            token = TokenManager(
                token_type=TokenType.ACCESS, encoded_token=provided_token
            )
            decoded_token = token.get_decoded_token()
        try:
            if not decoded_token:
                return []
            groups = decoded_token.get("cognito_groups", [])
            # Assuming groups is already a list of strings
            user_groups = groups if isinstance(groups, list) else []
            app.storage.user["user_groups"] = user_groups
            print("user_groups", user_groups)
            return user_groups
        except ClientError as e:
            print(f"Error fetching user groups: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error: {e}")
            return []

    def store_tokens(self, access_token, id_token, refresh_token, expiration_time):
        app.storage.user["access_token"] = access_token
        app.storage.user["id_token"] = id_token
        app.storage.user["refresh_token"] = refresh_token
        app.storage.user["expiration_time"] = expiration_time.isoformat()
        self.isAuthenticated = True

    def get_user_id(self, provided_token=None):
        if not provided_token:
            access_token = app.storage.user.get("access_token")
        else:
            access_token = provided_token
        token = TokenManager(TokenType.ACCESS, encoded_token=access_token)
        decoded_token = token.get_decoded_token()
        user_id = decoded_token.get("sub")
        return user_id

    def store_session(self, username, session_id, expiration_time, access_token=None):
        """
        Store the session details in DynamoDB.
        """
        if not access_token:
            user_id = self.get_user_id()
        else:
            user_id = self.get_user_id(access_token)
        if not user_id:
            print("User ID not found. Cannot store session.")
            return

        try:
            self.dynamodb_table.put_item(
                Item={
                    "session_id": session_id,
                    "user_id": user_id,
                    "expiration_time": int(expiration_time.timestamp()),
                    "created_at": int(datetime.now(timezone.utc).timestamp()),
                    "last_accessed": int(datetime.now(timezone.utc).timestamp()),
                    "is_active": True,
                }
            )
            print(f"Session {session_id} stored for user {username}.")
        except ClientError as e:
            print(f"Error storing session in DynamoDB: {e}")

    def verify_session(self, username, session_id):
        """
        Verify if the session is valid and not expired.
        """
        user_id = self.get_user_id()
        if not user_id:
            print("User ID not found. Cannot verify session.")
            return False

        try:
            response = self.dynamodb_table.get_item(
                Key={"session_id": session_id, "user_id": user_id}
            )
            item = response.get("Item")
            if not item:
                print("Session not found in DynamoDB.")
                return False

            current_timestamp = int(datetime.now(timezone.utc).timestamp())
            if current_timestamp > item.get("expiration_time", 0):
                print("Session has expired.")
                self.invalidate_session(username, session_id)
                self.signout()
                return False

            if not item.get("is_active", False):
                print("Session is inactive.")
                return False

            # Update last_accessed timestamp
            self.dynamodb_table.update_item(
                Key={"session_id": session_id, "user_id": user_id},
                UpdateExpression="SET last_accessed = :la",
                ExpressionAttributeValues={":la": current_timestamp},
            )
            return True
        except ClientError as e:
            print(f"Error verifying session in DynamoDB: {e}")
            return False

    def invalidate_session(self, username, session_id):
        """
        Invalidate the session by setting is_active to False and optionally deleting the session.
        """
        user_id = self.get_user_id()
        if not user_id:
            print("User ID not found. Cannot invalidate session.")
            return

        try:
            # Option 1: Mark session as inactive
            self.dynamodb_table.update_item(
                Key={"session_id": {"S": session_id}, "user_id": {"S": user_id}},
                UpdateExpression="SET is_active = :inactive",
                ExpressionAttributeValues={":inactive": False},
            )
            print(f"Session {session_id} invalidated for user {username}.")

        except ClientError as e:
            print(f"Error invalidating session in DynamoDB: {e}")

    def refresh_token(self):
        """Refresh tokens if access token is expired."""
        access_token = app.storage.user.get("access_token")
        expiration_time_str = app.storage.user.get("expiration_time")
        if expiration_time_str:
            expiration_time = datetime.fromisoformat(expiration_time_str)
            if datetime.now(timezone.utc) >= expiration_time:
                # Refresh the token
                refresh_token = app.storage.user.get("refresh_token")
                if refresh_token:
                    try:
                        response = self.client.initiate_auth(
                            ClientId=self.client_id,
                            AuthFlow="REFRESH_TOKEN_AUTH",
                            AuthParameters={"REFRESH_TOKEN": refresh_token},
                        )
                        authentication_result = response.get("AuthenticationResult")
                        if authentication_result:
                            # Generate a new session_id
                            session_id = str(uuid.uuid4())
                            app.storage.user["session_id"] = session_id

                            # Store new session in DynamoDB
                            new_expiration_time = datetime.now(
                                timezone.utc
                            ) + timedelta(hours=1)
                            self.store_session(
                                app.storage.user.get("username"),
                                session_id,
                                new_expiration_time,
                            )

                            self.store_tokens(
                                authentication_result.get("AccessToken"),
                                authentication_result.get("IdToken"),
                                authentication_result.get(
                                    "RefreshToken", refresh_token
                                ),  # Some providers may not return a new refresh token
                                new_expiration_time,
                            )
                    except ClientError as e:
                        print(f"Error refreshing tokens: {e}")
                        self.signout()
        return app.storage.user.get("access_token")

    def update_last_accessed(self, username, session_id):
        """
        Update the last_accessed timestamp for the session.
        """
        user_id = self.get_user_id()
        if not user_id:
            print("User ID not found. Cannot update session.")
            return

        try:
            current_timestamp = int(datetime.now(timezone.utc).timestamp())

            self.dynamodb_table.update_item(
                Key={"session_id": session_id, "user_id": user_id},
                UpdateExpression="SET last_accessed = :la",
                ExpressionAttributeValues={":la": current_timestamp},
            )
            print(f"Session {session_id} last_accessed updated for user {username}.")
        except ClientError as e:
            print(f"Error updating last_accessed in DynamoDB: {e}")

    def forgot_password(self, username):
        try:
            response = self.client.forgot_password(
                ClientId=self.client_id, Username=username
            )
            # Return the response, which may contain useful information
            return {"success": True, "response": response}
        except ClientError as e:
            print(f"Error in forgot_password: {e}")
            return {"success": False, "error": str(e)}

    def confirm_forgot_password(self, username, confirmation_code, new_password):
        try:
            response = self.client.confirm_forgot_password(
                ClientId=self.client_id,
                Username=username,
                ConfirmationCode=confirmation_code,
                Password=new_password,
            )
            # Check if the response contains any relevant information
            if response:
                print(f"Password reset response: {response}")
            return {"success": True, "message": "Password successfully reset"}
        except self.client.exceptions.CodeMismatchException:
            error_msg = "Invalid verification code provided, please try again."
            print(f"Error in confirm_forgot_password: {error_msg}")
            return {"success": False, "error": error_msg}
        except self.client.exceptions.ExpiredCodeException:
            error_msg = "Verification code has expired, please request a new one."
            print(f"Error in confirm_forgot_password: {error_msg}")
            return {"success": False, "error": error_msg}
        except self.client.exceptions.InvalidPasswordException as e:
            error_msg = f"Invalid password: {str(e)}"
            print(f"Error in confirm_forgot_password: {error_msg}")
            return {"success": False, "error": error_msg}
        except ClientError as e:
            error_msg = f"An error occurred: {str(e)}"
            print(f"Error in confirm_forgot_password: {error_msg}")
            return {"success": False, "error": error_msg}

    def get_users(self, company_id=None):
        try:
            response = self.client.list_users(UserPoolId=self.user_pool_id)
            users = response.get("Users", [])

            if company_id:
                # Filter users based on company_id attribute
                filtered_users = []
                for user in users:
                    attributes = {
                        attr["Name"]: attr["Value"]
                        for attr in user.get("Attributes", [])
                    }
                    if attributes.get("custom:company_id") == company_id:
                        filtered_users.append(user)
                return filtered_users
            else:
                return users
        except ClientError as e:
            print(f"Error fetching users: {e}")
            return []

    def get_all_custom_attributes(self, username):
        try:
            # Get user information from the user pool
            response = self.client.admin_get_user(
                UserPoolId=self.user_pool_id, Username=username
            )

            # Extract attributes
            attributes = response.get("UserAttributes", [])

            # Filter custom attributes (those prefixed with 'custom:')
            custom_attributes = {
                attr["Name"]: attr["Value"]
                for attr in attributes
                if attr["Name"].startswith("custom:")
            }

            return custom_attributes

        except self.client.exceptions.UserNotFoundException:
            return "User not found."
        except Exception as e:
            return f"An error occurred: {str(e)}"

    def update_user_attributes(self, username, attributes):
        """
        Update multiple user attributes in Cognito.

        Args:
            username (str): The username of the user to update.
            attributes (list): A list of dictionaries containing the attributes to update.
                               Each dictionary should have 'Name' and 'Value' keys.

        Returns:
            dict: A dictionary containing 'success' (bool) and 'message' (str) keys.
        """
        try:
            response = self.client.admin_update_user_attributes(
                UserPoolId=self.user_pool_id,
                Username=username,
                UserAttributes=attributes,
            )

            # Check if the response contains any relevant information
            if response:
                print(f"Update user response: {response}")

            return {
                "success": True,
                "message": f"Successfully updated attributes for user {username}",
            }
        except self.client.exceptions.UserNotFoundException:
            error_msg = f"User {username} not found in the user pool."
            print(f"Error in update_user_attributes: {error_msg}")
            return {"success": False, "error": error_msg}
        except ClientError as e:
            error_msg = f"An error occurred while updating user {username}: {str(e)}"
            print(f"Error in update_user_attributes: {error_msg}")
            return {"success": False, "error": error_msg}

    def create_user(
        self,
        email,
        given_name,
        family_name,
        phone_number,
        company_id,
        temporary_password,
    ):
        """
        Create a new user in the Cognito User Pool.

        Args:
            email (str): The email address for the new user (used as username).
            given_name (str): The user's given name.
            family_name (str): The user's family name.
            phone_number (str): The user's phone number.
            company_id (str): The user's company ID.
            temporary_password (str): A temporary password for the new user.

        Returns:
            dict: A dictionary containing 'success' (bool) and 'message' or 'error' (str) keys.
        """
        try:
            attributes = [
                {"Name": "email", "Value": email},
                {"Name": "email_verified", "Value": "true"},
                {"Name": "given_name", "Value": given_name},
                {"Name": "family_name", "Value": family_name},
                {"Name": "phone_number", "Value": phone_number},
                {"Name": "custom:company_id", "Value": company_id},
            ]

            response = self.client.admin_create_user(
                UserPoolId=self.user_pool_id,
                Username=email,
                UserAttributes=attributes,
                TemporaryPassword=temporary_password,
                MessageAction="SUPPRESS",
            )

            if response and response.get("User"):
                return {
                    "success": True,
                    "message": f"User {email} created successfully",
                    "user": response["User"],
                }
            else:
                return {
                    "success": False,
                    "error": "User creation response was unexpected",
                }

        except self.client.exceptions.UsernameExistsException:
            error_msg = f"User with email {email} already exists in the user pool."
            print(f"Error in create_user: {error_msg}")
            return {"success": False, "error": error_msg}

        except self.client.exceptions.InvalidPasswordException as e:
            error_msg = f"Invalid password: {str(e)}"
            print(f"Error in create_user: {error_msg}")
            return {"success": False, "error": error_msg}

        except ClientError as e:
            error_msg = (
                f"An error occurred while creating user with email {email}: {str(e)}"
            )
            print(f"Error in create_user: {error_msg}")
            return {"success": False, "error": error_msg}

    def add_user_to_group(self, username, group_name):
        """
        Add a user to a Cognito group.

        Args:
            username (str): The username (email) of the user to add to the group.
            group_name (str): The name of the group to add the user to.

        Returns:
            dict: A dictionary containing 'success' (bool) and 'message' or 'error' (str) keys.
        """
        try:
            response = self.client.admin_add_user_to_group(
                UserPoolId=self.user_pool_id, Username=username, GroupName=group_name
            )

            # If no exception is raised, the operation was successful
            return {
                "success": True,
                "message": f"User {username} successfully added to group {group_name}",
            }

        except self.client.exceptions.UserNotFoundException:
            error_msg = f"User {username} not found in the user pool."
            print(f"Error in add_user_to_group: {error_msg}")
            return {"success": False, "error": error_msg}

        except self.client.exceptions.ResourceNotFoundException:
            error_msg = f"Group {group_name} not found in the user pool."
            print(f"Error in add_user_to_group: {error_msg}")
            return {"success": False, "error": error_msg}

        except ClientError as e:
            error_msg = f"An error occurred while adding user {username} to group {group_name}: {str(e)}"
            print(f"Error in add_user_to_group: {error_msg}")
            return {"success": False, "error": error_msg}

    def remove_user_from_group(self, username, group_name):
        """
        Remove a user from a Cognito group.

        Args:
            username (str): The username (email) of the user to remove from the group.
            group_name (str): The name of the group to remove the user from.

        Returns:
            dict: A dictionary containing 'success' (bool) and 'message' or 'error' (str) keys.
        """
        try:
            response = self.client.admin_remove_user_from_group(
                UserPoolId=self.user_pool_id, Username=username, GroupName=group_name
            )

            # If no exception is raised, the operation was successful
            return {
                "success": True,
                "message": f"User {username} successfully removed from group {group_name}",
            }

        except self.client.exceptions.UserNotFoundException:
            error_msg = f"User {username} not found in the user pool."
            print(f"Error in remove_user_from_group: {error_msg}")
            return {"success": False, "error": error_msg}

        except self.client.exceptions.ResourceNotFoundException:
            error_msg = f"Group {group_name} not found in the user pool."
            print(f"Error in remove_user_from_group: {error_msg}")
            return {"success": False, "error": error_msg}

        except ClientError as e:
            error_msg = f"An error occurred while removing user {username} from group {group_name}: {str(e)}"
            print(f"Error in remove_user_from_group: {error_msg}")
            return {"success": False, "error": error_msg}

    @staticmethod
    def generate_password(length=12):
        import random
        import string

        """
        Generate a random password that meets AWS Cognito's minimum requirements.

        Args:
            length (int): The length of the password (default is 12).

        Returns:
            str: A randomly generated password.
        """
        if length < 8:
            length = 8  # Ensure minimum length of 8 characters

        # Define character sets
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = "!@#$%^&*()_+-=[]{}|'"

        # Ensure at least one character from each set
        password = [
            random.choice(lowercase),
            random.choice(uppercase),
            random.choice(digits),
            random.choice(special),
        ]

        # Fill the rest of the password
        for _ in range(length - 4):
            password.append(random.choice(lowercase + uppercase + digits + special))

        # Shuffle the password
        random.shuffle(password)

        return "".join(password)


def create_cognito_middleware():
    return CognitoMiddleware()
