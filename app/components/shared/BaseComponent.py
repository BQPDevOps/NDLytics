from nicegui import ui
from abc import ABC, abstractmethod


class BaseComponent(ABC):
    # def __init__(self):
    #     self.render()

    def refresh(self):
        """
        Refresh the component
        """
        self.render.refresh()

    @ui.refreshable
    def render(self):
        """
        Main render method that gets called on initialization.
        This method calls the content method which should be implemented by child classes.
        """
        self.content()

    @abstractmethod
    def content(self):
        """
        Abstract method that must be implemented by child classes.
        This is where the actual UI elements should be defined.
        """
        pass
