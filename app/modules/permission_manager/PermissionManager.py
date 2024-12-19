from modules import ListManager


class PermissionManager:
    """
    Manages permissions and roles for the application.

    This class provides methods to handle permission-related operations,
    including retrieving all permissions, checking if a permission exists,
    and getting cleaned permissions for specific roles.
    """

    PERMISSION_PREFIXES = ListManager().get_list("user_permissions")

    PERMISSION_SUFFIXES = ["view", "create", "edit", "delete"]

    ROLE_PERMISSIONS = ListManager().get_list("user_roles")

    @classmethod
    def get_all_permissions(cls):
        """
        Get a list of all possible permissions.

        Returns:
            list: A list of strings representing all possible permissions,
                  formed by combining each prefix with each suffix.
        """
        permissions = []
        for prefix in cls.PERMISSION_PREFIXES:
            for suffix in cls.PERMISSION_SUFFIXES:
                permissions.append(f"{prefix}_{suffix}")
        return sorted(permissions)

    @classmethod
    def permission_exists(cls, permission):
        """
        Check if a given permission exists.

        Args:
            permission (str): The permission string to check.

        Returns:
            bool: True if the permission exists, False otherwise.
        """
        if permission == "*":  # Special case for system admin
            return True
        try:
            prefix, suffix = permission.split("_")
            return (
                prefix in cls.PERMISSION_PREFIXES and suffix in cls.PERMISSION_SUFFIXES
            )
        except ValueError:
            return False

    @classmethod
    def get_all_roles(cls):
        """
        Get a list of all available roles.

        Returns:
            list: A list of strings representing all role names defined in ROLE_PERMISSIONS.
        """
        return sorted([role["role"] for role in cls.ROLE_PERMISSIONS])

    @classmethod
    def get_permissions(cls, role=None, prefix_only=False, cleaned_list=True):
        """
        Get a list of permissions, optionally filtered by role and cleaned.
        """
        # Find role in ROLE_PERMISSIONS list
        role_data = (
            next((r for r in cls.ROLE_PERMISSIONS if r["role"] == role), None)
            if role
            else None
        )
        if role and not role_data:
            return []

        # Handle system admin role
        if role_data and "*" in role_data["permissions"]:
            if prefix_only:
                return (
                    [
                        " ".join(p.split("_")).capitalize()
                        for p in cls.PERMISSION_PREFIXES
                    ]
                    if cleaned_list
                    else cls.PERMISSION_PREFIXES
                )
            return cls.get_all_permissions()

        # Get role-specific permissions
        if role_data:
            if prefix_only:
                prefixes = [p["prefix"] for p in role_data["permissions"]]
                return (
                    [" ".join(p.split("_")).capitalize() for p in prefixes]
                    if cleaned_list
                    else prefixes
                )

            permissions = []
            for perm in role_data["permissions"]:
                prefix = perm["prefix"]
                for suffix in perm["suffixes"]:
                    if cleaned_list:
                        perm_str = f"{' '.join(prefix.split('_')).capitalize()} {suffix.capitalize()}"
                    else:
                        perm_str = f"{prefix}_{suffix}"
                    permissions.append(perm_str)
            return sorted(permissions)

        # If no role specified, return all possible permissions
        if prefix_only:
            return (
                [" ".join(p.split("_")).capitalize() for p in cls.PERMISSION_PREFIXES]
                if cleaned_list
                else cls.PERMISSION_PREFIXES
            )

        return cls.get_all_permissions()
