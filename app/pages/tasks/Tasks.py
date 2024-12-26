from nicegui import ui
from core import StandardPage
from .components import *
from components import ActionBar
from .components.ListView import ListViewComponent
from .components.NewTaskForm import NewTaskFormComponent
from .components.KanbanView import KanbanViewComponent
from middleware.dynamo import DynamoMiddleware
from middleware.cognito import CognitoMiddleware
from config import config


class TasksPage(StandardPage):
    def __init__(self, session_manager):
        super().__init__(
            session_manager,
            page_config={
                "page_title": "Tasks",
                "page_icon": "tasks",
                "page_route": "/tasks",
                "page_root_route": "/",
                "page_description": "Tasks",
                "nav_position": "top",
            },
        )
        self.dynamo_middleware = DynamoMiddleware(config.aws_tasks_table_name)
        self.cognito_middleware = CognitoMiddleware()
        self.state = {
            "active_view": "list",
            "selected_task": None,
            "tasks": self._get_tasks(),
        }
        self.new_task_form = NewTaskFormComponent(on_task_created=self.refresh_tasks)

    def _get_tasks(self):
        user_id = self.cognito_middleware.get_user_id()

        # Get user's own tasks
        own_tasks_expression = {":uid": {"S": user_id}}
        own_tasks_response = self.dynamo_middleware.scan(
            filter_expression="user_id = :uid",
            expression_attribute_values=own_tasks_expression,
        )

        # Get tasks where user is tagged
        tagged_tasks_expression = {":uid": {"S": user_id}}
        tagged_tasks_response = self.dynamo_middleware.scan(
            filter_expression="contains(task_tags, :uid)",
            expression_attribute_values=tagged_tasks_expression,
        )

        # Combine and deduplicate tasks
        all_tasks = []
        seen_task_ids = set()

        # Add own tasks
        if "Items" in own_tasks_response:
            for task in own_tasks_response["Items"]:
                task_id = task["task_id"]["S"]
                if task_id not in seen_task_ids:
                    all_tasks.append(task)
                    seen_task_ids.add(task_id)

        # Add tagged tasks
        if "Items" in tagged_tasks_response:
            for task in tagged_tasks_response["Items"]:
                task_id = task["task_id"]["S"]
                if task_id not in seen_task_ids:
                    all_tasks.append(task)
                    seen_task_ids.add(task_id)

        return {"Items": all_tasks}

    def switch_view(self, view):
        self.state["active_view"] = view
        self.render_content.refresh()

    def on_select_task(self, task):
        self.state["selected_task"] = task
        self.render_content.refresh()

    def refresh_tasks(self):
        self.state["tasks"] = self._get_tasks()
        self.render_content.refresh()

    @ui.refreshable
    def render_content(self):
        with ui.element("transition").props(
            "appear enter-active-class='animated fadeIn' leave-active-class='animated fadeOut'"
        ).classes("w-full"):
            if self.state["active_view"] == "list":
                with ui.element("div").classes("list-container").style("width: 100%"):
                    ListViewComponent(self.state, self.on_select_task).render()

            elif self.state["active_view"] == "kanban":
                with ui.element("div").classes("kanban-container").style("width: 100%"):
                    KanbanViewComponent(
                        self.state, on_task_updated=self.refresh_tasks
                    ).render()

    def page_content(self):
        with ui.column().classes("w-full h-full p-4"):
            with ui.row().style("width:100%;"):
                ActionBar(
                    views=[
                        {"label": "List", "value": "list"},
                        {"label": "Kanban", "value": "kanban"},
                    ],
                    active_view=self.state["active_view"],
                    on_view_switch=self.switch_view,
                    actions=[
                        {
                            "icon": "add",
                            "label": "Add",
                            "on_click": lambda: self.new_task_form.open(),
                        }
                    ],
                ).render()
            self.render_content()


def tasks_page(session_manager):
    page = TasksPage(session_manager)
    page.render()
