from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Footer, Header, Label

from nike import NikeApi
from gpx_exporter import GpxExporter

from widgets import BearerTokenWidget, Controls, ErrorMessageLabel, NikeActivityItem, NikeActivitiesList

class NrcToStravaApp(App):
    CSS_PATH = "main.css" # Load the css file when the app starts
    TITLE = "NRC to Strava"

    def __init__(self):
        self.gpx_exporter = GpxExporter()
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
            yield Controls()

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

    def on_controls_paginated(self, message: Controls.Paginated) -> None:
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

    def on_controls_exported_activities(self) -> None:
        nike_activities_list = self.query_one(NikeActivitiesList)
        self.gpx_exporter.export_activities(nike_activities_list.selected_activities)

if __name__ == "__main__":
    app = NrcToStravaApp()
    app.run()
