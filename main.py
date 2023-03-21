from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.message import Message, MessageTarget
from textual.widgets import Button, Header, Input, Label, TextLog, Static
import requests

class BearerTokenWidget(Static):
    class TokenUpdated(Message):
        def __init__(self, bearer_token: str) -> None:
            self.bearer_token = bearer_token
            super().__init__()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        input = self.query_one("#bearer-token-input", Input)
        button_id = event.button.id

        if button_id == "bearer-token-widget-continue-button":
            self.post_message(self.TokenUpdated(input.value))
        elif button_id == "bearer-token-widget-clear-button":
            # Clear the bearer token input
            input.action_end()
            input.action_delete_left_all()
            input.focus()

    def compose(self) -> ComposeResult:
        yield Input(
            placeholder="Bearer ...",
            id="bearer-token-input",
        )
        with Static(id="bearer-token-widget-button-container"):
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

    # Constructs UI and widgets
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="app-container"):
            yield Label("Sign into Nike from your web browser, and using the developer tools, retrieve the access token from the request header (\"Authentication\") of any api.nike.com request.")
            yield BearerTokenWidget()
            yield TextLog()

    def on_bearer_token_widget_token_updated(self, message: BearerTokenWidget.TokenUpdated) -> None:
        response = requests.get(
            "https://api.nike.com/plus/v3/activities/before_id/v3/*",
            params={
                "limit": "10",
                "types": "run,jogging",
                "include_deleted": "false",
            },
            headers={
                "Authorization": message.bearer_token,
            }
        )

        text_log = self.query_one(TextLog)
        text_log.write(response.text)

if __name__ == "__main__":
    app = NrcToStravaApp()
    app.run()
