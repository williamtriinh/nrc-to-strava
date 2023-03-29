import requests

from .constants import PAGE_SIZE

class NikeApi:
    
    bearer_token: str | None = None

    @staticmethod
    def fetch_activities(before_id: str = "*") -> any:
        response = requests.get(
            f"https://api.nike.com/plus/v3/activities/before_id/v3/{before_id}",
            params={
                "limit": str(PAGE_SIZE),
                "types": "run,jogging",
                "include_deleted": "false",
            },
            headers={
                "Authorization": NikeApi.bearer_token,
            }
        )

        return response.json()
    
    @staticmethod
    def fetch_activity(activity_id: str) -> any:
        response = requests.get(
            f"https://api.nike.com/plus/v3/activity/v3/{activity_id}",
            params={
                "metrics": "all",
            },
            headers={
                "Authorization": NikeApi.bearer_token,
            }
        )

        return response.json()
