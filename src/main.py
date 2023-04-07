from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Footer, Header, Label, TextLog

from nike import NikeApi
from gpx_exporter import GpxExporter

from widgets import BearerTokenWidget, Controls, ErrorMessageLabel, NikeActivitiesList

class NrcToStravaApp(App):
    CSS_PATH = "main.css" # Load the css file when the app starts
    TITLE = "NRC to Strava"

    def __init__(self):
        self.gpx_exporter = GpxExporter()

        self.nike_activities_list: NikeActivitiesList
        self.error_log: TextLog

        super().__init__()

    # Constructs UI and widgets
    def compose(self) -> ComposeResult:
        self.nike_activities_list = NikeActivitiesList()
        self.error_log = TextLog()

        yield Header()
        yield Footer()
        with Vertical(id="app-container"):
            yield Label("Sign into Nike from your web browser, and using the developer tools, retrieve the access token from the request header (\"Authentication\") of any api.nike.com request.")
            yield BearerTokenWidget()
            yield self.nike_activities_list
            yield Controls()
            yield self.error_log

    def on_bearer_token_widget_token_updated(self, message: BearerTokenWidget.TokenUpdated) -> None:
        try:
            NikeApi.bearer_token = message.bearer_token
            data = NikeApi.fetch_activities()

            nike_activities_list = self.query_one(NikeActivitiesList)
            nike_activities_list.activities = data["activities"]
            nike_activities_list.pages = ["*", data["paging"]["before_id"]]

        except Exception as error:
            self.error_log.write(error)

    def on_controls_paginated(self, message: Controls.Paginated) -> None:
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
            self.error_log.write(error)

    def on_controls_exported_activities(self) -> None:
        self.gpx_exporter.export_activities(self.nike_activities_list.selected_activities)
        self.nike_activities_list.selected_activities = set()

    def on_controls_unselected_all_activities(self) -> None:
        self.nike_activities_list.selected_activities = set()

if __name__ == "__main__":
    app = NrcToStravaApp()
    app.run()
