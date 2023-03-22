from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.containers import Grid, Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, Footer, Header, Input, Label, ListItem, ListView
import requests

PAGE_SIZE: int = 25

class ErrorMessageLabel(Label):

    error_message: reactive[str] = reactive("", layout=True)

    def render(self) -> str:
        return self.error_message

class NikeActivityItem(ListItem):

    def __init__(self, activity: any) -> None:
        self.activity = activity
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Label("Jun 8, 2023, 07:16PM")
        yield Label("Avg. Distance: ")

class NikeActivitiesList(ListView):

    activities: reactive[list: any] = reactive([])
    pages: reactive[list: str] = reactive(["*"])

    # Remove existing items from the list and new items associated to the
    # new activities
    async def watch_activities(self, new_activities: any) -> None:
        self.clear()
        for activity in new_activities:
            self.append(NikeActivityItem(activity))

class BearerTokenWidget(Vertical):

    # Custom message for when the bearer token is updated
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

    # Constructs UI and widgets
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with Vertical(id="app-container"):
            yield Label("Sign into Nike from your web browser, and using the developer tools, retrieve the access token from the request header (\"Authentication\") of any api.nike.com request.")
            yield BearerTokenWidget()
            yield ErrorMessageLabel()
            yield NikeActivitiesList()

    def on_bearer_token_widget_token_updated(self, message: BearerTokenWidget.TokenUpdated) -> None:
        error_message_label = self.query_one(ErrorMessageLabel)
        error_message_label.error_message = ""
        
        try:
            response = requests.get(
                "https://api.nike.com/plus/v3/activities/before_id/v3/*",
                params={
                    "limit": str(PAGE_SIZE),
                    "types": "run,jogging",
                    "include_deleted": "false",
                },
                headers={
                    "Authorization": message.bearer_token,
                }
            )
            response.raise_for_status()
            json = response.json()
            nike_activities_list = self.query_one(NikeActivitiesList)
            nike_activities_list.activities = json["activities"]
        except Exception as error:
            error_message_label.error_message = str(error)

if __name__ == "__main__":
    app = NrcToStravaApp()
    app.run()
