import math

from textual.app import App, ComposeResult
from textual.reactive import reactive, var
from textual.containers import Grid, Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, Checkbox, Footer, Header, Input, Label, ListItem, ListView, TextLog
from datetime import datetime

from nike import NikeApi
from gpx_exporter import GpxExporter

from constants import PAGE_SIZE

gpx_exporter = GpxExporter()

class ErrorMessageLabel(Label):

    DEFAULT_CLASSES = "hidden"

    error_message: reactive[str] = reactive("", layout=True)

    def render(self) -> str:
        return self.error_message

class NikeActivityItem(ListItem):

    class AddedToExport(Message):
        def __init__(self, activity: any):
            self.activity = activity
            super().__init__()

    class RemovedFromExport(Message):
        def __init__(self, activity_id: str):
            self.activity_id = activity_id
            super().__init__()

    def __init__(self, activity: any, index: int, is_exported: bool = False) -> None:
        self.activity: any = activity
        self.index: int = index
        self.is_exported: bool = is_exported

        self.activity_name: str = activity["tags"]["com.nike.name"]
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
            self.post_message(self.AddedToExport(self.activity))
        else:
            self.post_message(self.RemovedFromExport(self.activity["id"]))

    def _duration_formatted_time(self) -> str:
        seconds = math.floor((self.duration_ms / 1000) % 60)
        minutes = math.floor((self.duration_ms / 60000) % 60)
        hours = math.floor(self.duration_ms / 3600000)
        return "{:3.0f}:{:02.0f}:{:02.0f}".format(hours, minutes, seconds)

class NikeActivitiesList(ListView):

    activities: reactive[list: any] = reactive([])
    current_page: int = reactive(0)
    pages: reactive[list: str] = reactive([])

    # Remove existing items from the list and new items associated to the
    # new activities
    async def watch_activities(self, new_activities: any) -> None:
        self.clear()
        for index, activity in enumerate(new_activities):
            self.append(NikeActivityItem(
                activity,
                index + self.current_page * PAGE_SIZE,
                is_exported = gpx_exporter.does_activity_exist(activity["id"])
            ))

class NikeActivitiesListPageButtons(Horizontal):

    class Paginated(Message):
        def __init__(self, direction: int) -> None:
            self.direction = direction
            super().__init__()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        button_id = event.button.id

        if button_id == "prev-button":
            self.post_message(self.Paginated(-1))
        elif button_id == "next-button":
            self.post_message(self.Paginated(1))
        elif button_id == "export-button":
            gpx_exporter.export_activities()

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

class NrcToStravaApp(App):

    # Load the css file when the app starts
    CSS_PATH = "main.css"
    TITLE = "NRC to Strava"

    def __init__(self):
        super().__init__()

    # Constructs UI and widgets
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with Vertical(id="app-container"):
            yield Label("Sign into Nike from your web browser, and using the developer tools, retrieve the access token from the request header (\"Authentication\") of any api.nike.com request.")
            yield BearerTokenWidget()
            yield ErrorMessageLabel()
            yield NikeActivitiesList()
            yield NikeActivitiesListPageButtons()

    def on_bearer_token_widget_token_updated(self, message: BearerTokenWidget.TokenUpdated) -> None:
        error_message_label = self.query_one(ErrorMessageLabel)
        error_message_label.error_message = ""
        error_message_label.add_class("hidden")

        try:
            NikeApi.bearer_token = message.bearer_token
            data = NikeApi.fetch_activities()

            nike_activities_list = self.query_one(NikeActivitiesList)
            nike_activities_list.activities = data["activities"]
            nike_activities_list.pages = ["*", data["paging"]["before_id"]]

        except Exception as error:
            error_message_label.error_message = str(error)
            error_message_label.remove_class("hidden")

    def on_nike_activities_list_page_buttons_paginated(self, message: NikeActivitiesListPageButtons.Paginated) -> None:
        error_message_label = self.query_one(ErrorMessageLabel)
        error_message_label.error_message = ""
        error_message_label.add_class("hidden")

        try:
            nike_activities_list = self.query_one(NikeActivitiesList)

            new_page: int = max(0, min(nike_activities_list.current_page + message.direction, len(nike_activities_list.pages) - 1))
            if new_page == nike_activities_list.current_page:
                return

            before_id: str = nike_activities_list.pages[new_page]

            data = NikeApi.fetch_activities(before_id)

            nike_activities_list.current_page = new_page
            nike_activities_list.activities = data["activities"]

            # Add the next page to our list of pages if we're on the last page
            if new_page == len(nike_activities_list.pages) - 1 and data["paging"] and data["paging"]["before_id"]:
                nike_activities_list.pages = [*nike_activities_list.pages, data["paging"]["before_id"]]

        except Exception as error:
            error_message_label.error_message = str(error)
            error_message_label.remove_class("hidden")

    def on_nike_activity_item_added_to_export(self, message: NikeActivityItem.AddedToExport) -> None:
        gpx_exporter.activities_to_export.add(message.activity["id"])

    def on_nike_activity_item_removed_from_export(self, message: NikeActivityItem.RemovedFromExport) -> None:
        gpx_exporter.activities_to_export.remove(message.activity_id)


if __name__ == "__main__":
    app = NrcToStravaApp()
    app.run()
