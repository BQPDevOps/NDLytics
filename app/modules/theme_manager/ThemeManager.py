class ThemeManager:
    """
    Manages color themes for an analytics website.

    Provides easy access to primary, secondary, and accent colors with variations
    for hover states, box shadows, highlights, and borders.
    """

    def __init__(self, theme="default_basic"):
        """
        Initializes the ThemeManager with a specified theme.

        Args:
            theme (str): The name of the theme to use.
                         Currently supports "default" (default).
        """
        self.theme = theme
        self.colors = self._get_theme_colors(theme)

    def _get_theme_colors(self, theme):
        """
        Returns a dictionary of color values for the specified theme.
        """
        if theme == "default":
            return {
                "primary": {
                    "base": "#232323",
                    "base_light": "#4E4E4E",
                    "base_dark": "#1C1C1C",
                    "hover_light": "#3d3d3d",
                    "hover_dark": "#1a1a1a",
                    "box_shadow": "rgba(35, 35, 35, 0.3)",
                    "box_shadow_inset": "rgba(35, 35, 35, 0.5)",
                    "highlight": "#2d2d2d",
                    "border_light": "#404040",
                    "border_dark": "#171717",
                },
                "secondary": {
                    "base": "#E4BD50",
                    "base_light": "#E3C159",
                    "base_dark": "#B08E26",
                    "hover_light": "#eac870",  # Lighten base by 10%
                    "hover_dark": "#ddb230",  # Darken base by 10%
                    "box_shadow": "rgba(228, 189, 80, 0.3)",  # Base with 0.3 opacity
                    "box_shadow_inset": "rgba(228, 189, 80, 0.5)",  # Base with 0.5 opacity
                    "highlight": "#e9c55f",  # Slightly lighter than base
                    "border_light": "#ecd083",  # Lighter than base
                    "border_dark": "#d4aa2d",  # Darker than base
                },
                "controls": {
                    "buttons": {
                        "primary": {
                            "base": "#E4BD50",
                            "base_dark": "#B08E26",
                            "hover_light": "#eac870",  # Lighten base by 10%
                            "hover_dark": "#ddb230",  # Darken base by 10%
                            "box_shadow": "rgba(228, 189, 80, 0.3)",  # Base with 0.3 opacity
                            "box_shadow_inset": "rgba(228, 189, 80, 0.5)",  # Base with 0.5 opacity
                            "highlight": "#e9c55f",  # Slightly lighter than base
                            "border_light": "#ecd083",  # Lighter than base
                            "border_dark": "#d4aa2d",  # Darker than base
                        },
                        "secondary": {
                            "base": "#333333",
                            "base_dark": "#262626",  # Darker than base
                            "hover_light": "#4d4d4d",  # Lighten base by 10%
                            "hover_dark": "#1a1a1a",  # Darken base by 10%
                            "box_shadow": "rgba(51, 51, 51, 0.3)",  # Base with 0.3 opacity
                            "box_shadow_inset": "rgba(51, 51, 51, 0.5)",  # Base with 0.5 opacity
                            "highlight": "#404040",  # Slightly lighter than base
                            "border_light": "#4d4d4d",  # Lighter than base
                            "border_dark": "#1a1a1a",  # Darker than base
                        },
                    },
                    "label": {
                        "primary": {
                            "base": "#FFFFFF",
                        }
                    },
                    "actionbar": {
                        "primary": {
                            "base": "#5898d4",
                        },
                    },
                },
                "base-color": {
                    "white": "#FFFFFF",
                    "black": "#000000",
                    "gray": "#808080",
                },
            }
        elif theme == "default_basic":
            return {
                "primary": {
                    "base": "#BDB334",
                    "accents": {
                        "light": {"base": "#AFA888"},
                        "dark": {"base": "#956343"},
                    },
                    "shades": {
                        "light": {"base": "#F6F6F5"},
                        "dark": {"base": "#39323F"},
                    },
                },
                "secondary": {
                    "base": "#232323",
                    "accents": {
                        "light": {"base": "#7F7B7A"},
                        "dark": {"base": "#6D6D6F"},
                    },
                    "shades": {
                        "light": {"base": "#EEEAEB"},
                        "dark": {"base": "#161115"},
                    },
                },
                "basic": {
                    "white": "#FFFFFF",
                    "black": "#000000",
                    "gray": "#808080",
                },
                "ui": {
                    "primary": {
                        "base": "#C5B632",
                    },
                    "info": {
                        "base": "#3B2A37",
                    },
                    "success": {
                        "base": "#70B147",
                    },
                    "warning": {
                        "base": "#EEA10F",
                    },
                    "danger": {
                        "base": "#F44336",
                    },
                },
            }
        else:
            raise ValueError(f"Unsupported theme: {theme}")

    def get_color(self, color_path):
        """
        Returns the hex code for the specified color path.

        Args:
            color_path (str): The path to the color in dot notation
                             (e.g. "text.header.h1" or "primary.base")

        Returns:
            str: The hex code of the color.
        """
        keys = color_path.split(".")
        value = self.colors
        for key in keys:
            value = value[key]
        return value
