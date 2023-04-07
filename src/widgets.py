import os
import math

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, Checkbox, Input, Label, ListItem, ListView
from datetime import datetime

from constants import PAGE_SIZE

class ErrorMessageLabel(Label):
    DEFAULT_CLASSES = "hidden"

    error_message: reactive[str] = reactive("", layout=True)

    def render(self) -> str:
        return self.error_message

class NikeActivityItem(ListItem):
    class Selected(Message):
        def __init__(self, activity_id: any):
            self.activity_id = activity_id
            super().__init__()

    class Unselected(Message):
        def __init__(self, activity_id: str):
            self.activity_id = activity_id
            super().__init__()

    def __init__(self, activity: any, index: int, is_exported: bool = False) -> None:
        self.activity: any = activity
        self.index: int = index
        self.is_exported: bool = is_exported

        self.activity_name: str = activity["tags"].get("com.nike.name", "No name")
        self.date: datetime = datetime.fromtimestamp(activity["start_epoch_ms"] / 1000)
        self.distance: float = 0.0
        self.pace: float = 0.0
        self.duration_ms: int = activity["active_duration_ms"]

        # Parse activity summary data
        for summary in activity["summaries"]:
            if summary["metric"] == "distance":
                self.distance = math.floor(summary["value"] * 100) / 100
            elif summary["metric"] == "pace":
                self.pace = math.floor(summary["value"] * 100) / 100

        super().__init__()

    def compose(self) -> ComposeResult:
        yield Label("{:3.0f}.".format(self.index + 1))
        yield Label(self.date.strftime("%x - %X"))
        yield Label("{:25.25}".format(self.activity_name))
        yield Label("{:6.2f} KM".format(self.distance))
        yield Label("{:5.2f} MIN/KM".format(self.pace))
        yield Label(self._duration_formatted_time())
        yield Checkbox("Export", value = self.is_exported)

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        event.stop()
        if event.value:
            self.post_message(self.Selected(self.activity["id"]))
        else:
            self.post_message(self.Unselected(self.activity["id"]))

    def _duration_formatted_time(self) -> str:
        seconds = math.floor((self.duration_ms / 1000) % 60)
        minutes = math.floor((self.duration_ms / 60000) % 60)
        hours = math.floor(self.duration_ms / 3600000)
        return "{:3.0f}:{:02.0f}:{:02.0f}".format(hours, minutes, seconds)

class NikeActivitiesList(ListView):
    activities: reactive[list: any] = reactive([])
    selected_activities: reactive[set[str]] = reactive(set())
    current_page: int = reactive(0)
    pages: reactive[list: str] = reactive([])

    # Remove existing items from the list and new items associated to the
    # new activities
    def watch_activities(self, new_activities: list[any]) -> None:
        self._updated_activity_list_items(new_activities)

    def watch_selected_activities(self, new_selected_activities: set[str]) -> None:
        if len(new_selected_activities) == 0:
            self._updated_activity_list_items(self.activities)

    def on_nike_activity_item_selected(self, message: NikeActivityItem.Selected) -> None:
        self.selected_activities = self.selected_activities.union({ message.activity_id })

    def on_nike_activity_item_unselected(self, message: NikeActivityItem.Unselected) -> None:
        self.selected_activities = self.selected_activities.difference({ message.activity_id })

    def _updated_activity_list_items(self, activities: any) -> None:
        self.clear()
        for index, activity in enumerate(activities):
            self.append(NikeActivityItem(
                activity,
                index + self.current_page * PAGE_SIZE,
                activity["id"] in self.selected_activities
            ))

class Controls(Horizontal):
    class Paginated(Message):
        def __init__(self, direction: int) -> None:
            self.direction = direction
            super().__init__()

    class ExportedActivities(Message):
        pass

    class UnselectedAllActivities(Message):
        pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        button_id = event.button.id

        if button_id == "prev-button":
            self.post_message(self.Paginated(-1))
        elif button_id == "next-button":
            self.post_message(self.Paginated(1))
        elif button_id == "export-button":
            self.post_message(self.ExportedActivities())
        elif button_id == "delete-exports-button":
            if not os.path.exists("./exports"):
                os.mkdir("./exports")
                return

            entries = os.listdir("./exports")
            for entry in entries:
                os.remove(f"./exports/{entry}")
        elif button_id == "unselect-all-button":
            self.post_message(self.UnselectedAllActivities())

    def compose(self) -> ComposeResult:
        yield Button(
            "Prev",
            id="prev-button",
        )
        yield Button(
            "Next",
            id="next-button",
        )
        yield Button(
            "Export Selected Activities",
            id="export-button",
        )
        yield Button(
            "Delete All Exports",
            id="delete-exports-button",
        )
        yield Button(
            "Unselect All",
            id="unselect-all-button",
        )

class BearerTokenWidget(Vertical):
    # Custom message for when the bearer token is updated
    class TokenUpdated(Message):
        def __init__(self, bearer_token: str) -> None:
            self.bearer_token = bearer_token
            super().__init__()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()

        input = self.query_one("#bearer-token-input", Input)
        button_id = event.button.id

        if button_id == "bearer-token-widget-continue-button":
            self.post_message(self.TokenUpdated(input.value))
        elif button_id == "bearer-token-widget-clear-button":
            # Clear the bearer token input
            input.action_end()
            input.action_delete_left_all()
            input.focus()

    def on_mount(self) -> None:
        # Focus the bearer token input when mounted
        input = self.query_one(Input)
        input.focus()

    def compose(self) -> ComposeResult:
        yield Input(
            placeholder="Bearer ...",
            id="bearer-token-input",
        )
        with Horizontal(id="bearer-token-widget-button-container"):
            yield Button(
                label="Continue",
                id="bearer-token-widget-continue-button",
            )
            yield Button(
                label="Clear",
                id="bearer-token-widget-clear-button",
            )
