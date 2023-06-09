import requests

from constants import NIKE_ACTIVITIES_URL, NIKE_ACTIVITY_URL, PAGE_SIZE

class NikeApi:
    
    bearer_token: str | None = None

    @staticmethod
    def fetch_activities(before_id: str = "*") -> any:
        response = requests.get(
            f"{NIKE_ACTIVITIES_URL}/{before_id}",
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
            f"{NIKE_ACTIVITY_URL}/{activity_id}",
            params={
                "metrics": "all",
            },
            headers={
                "Authorization": NikeApi.bearer_token,
            }
        )

        return response.json()
