import requests

from constants import PAGE_SIZE

class NikeApi:
    
    def __init__(self):
        self.bearer_token: str | None = None

    def fetch_activities(self, before_id: str = "*") -> any:
        response = requests.get(
            f"https://api.nike.com/plus/v3/activities/before_id/v3/{before_id}",
            params={
                "limit": str(PAGE_SIZE),
                "types": "run,jogging",
                "include_deleted": "false",
            },
            headers={
                "Authorization": self.bearer_token,
            }
        )

        return response.json()
