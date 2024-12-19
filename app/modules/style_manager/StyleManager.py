import uuid


class StyleManager:
    def __init__(self):
        self._id = str(uuid.uuid4())
        self._styles = {
            "standard_page": {
                "page_container": """
                    gap:0;
                    padding:0;
                    margin:0;
                    position: relative;
                    border-radius:20px;
                    width:100%;
                    height:96vh;
                    border:1px solid rgba(192,192,192,0.4);
                    """,
                "page_background": """
                    position:absolute;
                    width:100%;
                    height:100%;
                    overflow:hidden;
                    top:0;
                    left:0;
                    """,
                "page_background_image": """
                    opacity:0.5;
                    filter:blur(2px);
                    top:0;
                    left:0;
                    z-index:-1;
                    position:absolute;
                    """,
                "drawer_container": """
                    width:100%;
                    height:100%;
                    background-color:#FFFFFF;
                    border-radius:10px;
                    border:1px solid rgba(192,192,192,0.3);
                    box-shadow:0 0 0 1px rgba(192,192,192,0.4);
                    """,
                "page_navbar": """
                    width:100%;
                    height:4rem;
                    border-radius:10px 10px 0 0;
                    border:1px solid rgba(192,192,192,0.3);
                    display:flex;
                    justify-content:center;
                    padding-right:0.5rem;
                    padding-left:0.5rem;
                    flex-direction:row;
                    """,
                "page_navbar_branding": """
                    width:80%;
                    height:2rem;
                    """,
            }
        }

    def set_styles(self, styles: dict):
        self._styles = styles

    def add_style(self, style_name: str, style_value: str):
        self._styles[style_name] = style_value

    def remove_style(self, style_name: str):
        if style_name in self._styles:
            del self._styles[style_name]

    def get_style(self, style_name: str) -> str:
        if "." in style_name:
            parent, child = style_name.split(".")
            return self._styles.get(parent, {}).get(child, "")
        return self._styles.get(style_name, "")
