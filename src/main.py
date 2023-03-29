import os
import math

from textual.app import App, ComposeResult
from textual.reactive import reactive, var
from textual.containers import Grid, Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, Checkbox, Footer, Header, Input, Label, ListItem, ListView, TextLog
from datetime import datetime

from .nike import NikeApi
from .gpx_exporter import GpxExporter

from .widgets import BearerTokenWidget, ErrorMessageLabel, NikeActivityItem, NikeActivitiesList, NikeActivitiesListPageButtons

from .constants import PAGE_SIZE

gpx_exporter = GpxExporter()

class NrcToStravaApp(App):
    CSS_PATH = "main.css" # Load the css file when the app starts
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
