user_roles_list = [
    {"role": "_role_system_admin", "permissions": ["*"]},
    {
        "role": "_role_company_admin",
        "permissions": [
            {"prefix": "dashboard", "suffixes": ["view", "create", "edit", "delete"]},
            {"prefix": "campaigns", "suffixes": ["view", "create", "edit", "delete"]},
            {"prefix": "filemanager", "suffixes": ["view", "create", "edit", "delete"]},
            {"prefix": "settings", "suffixes": ["view", "edit"]},
        ],
    },
    {
        "role": "_role_company_user",
        "permissions": [
            {"prefix": "dashboard", "suffixes": ["view", "create", "edit", "delete"]},
            {"prefix": "settings", "suffixes": ["view", "edit"]},
        ],
    },
]
