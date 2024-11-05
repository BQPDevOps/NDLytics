class ThemeManager:
    """
    Manages color themes for an analytics website.

    Provides easy access to primary, secondary, and accent colors with variations
    for hover states, box shadows, highlights, and borders.
    """

    def __init__(self, theme="deep_blue"):
        """
        Initializes the ThemeManager with a specified theme.

        Args:
            theme (str): The name of the theme to use.
                         Currently supports "deep_blue" (default).
        """
        self.theme = theme
        self.colors = self._get_theme_colors(theme)

    def _get_theme_colors(self, theme):
        """
        Returns a dictionary of color values for the specified theme.
        """
        if theme == "deep_blue":
            return {
                "primary": {
                    "base": "#004466",
                    "hover": "#005580",
                    "box_shadow": "rgba(0, 68, 102, 0.3)",
                    "highlight": "#0077CC",
                    "border": "#003355",
                },
                "secondary": {
                    "base": "#808080",
                    "hover": "#999999",
                    "box_shadow": "rgba(128, 128, 128, 0.2)",
                    "highlight": "#B3B3B3",
                    "border": "#666666",
                },
                "accent": {
                    "base": "#FF7F50",
                    "hover": "#FF9966",
                    "box_shadow": "rgba(255, 127, 80, 0.4)",
                    "highlight": "#FF6600",
                    "border": "#CC6633",
                },
                "button-basic": {
                    "base": "#007bff",
                    "hover": "#0056b3",
                    "box_shadow": "rgba(0, 123, 255, 0.3)",
                    "highlight": "#007bff",
                    "border": "#0056b3",
                    "text": "#FFFFFF",
                },
                "success": {
                    "base": "#00CC00",
                    "hover": "#00E600",
                    "box_shadow": "rgba(0, 204, 0, 0.3)",
                    "highlight": "#00FF00",
                    "border": "#009900",
                },
                "error": {
                    "base": "#FF0000",
                    "hover": "#FF3333",
                    "box_shadow": "rgba(255, 0, 0, 0.3)",
                    "highlight": "#FF4D4D",
                    "border": "#CC0000",
                },
                "background": {"base": "#EEF4FA", "light": "#FFFFFF"},
                "text": {
                    "base": "#FFFFFF",
                    "light": "#333333",
                    "header": {
                        "h1": "#FFFFFF",
                        "h2": "#E0F2F7",
                        "h3": "#90CAF9",
                        "h4": "#90CAF9",
                        "h5": "#90CAF9",
                        "h6": "#90CAF9",
                    },
                },
                "basic": {
                    "white": "#FFFFFF",
                    "black": "#000000",
                    "gray": "#808080",
                    "red": "#FF0000",
                    "green": "#00FF00",
                    "blue": "#0000FF",
                    "yellow": "#FFFF00",
                    "purple": "#800080",
                    "orange": "#FFA500",
                    "pink": "#FFC0CB",
                    "brown": "#A52A2A",
                },
            }
        else:
            raise ValueError(f"Unsupported theme: {theme}")

    def get_color(self, color_type, variation="base"):
        """
        Returns the hex code for the specified color and variation.

        Args:
            color_type (str): The type of color
                                ("primary", "secondary", "accent", etc.).
            variation (str): The variation of the color
                                ("base", "hover", "box_shadow", etc.).
                                Defaults to "base".

        Returns:
            str: The hex code of the color.
        """
        return self.colors[color_type][variation]
