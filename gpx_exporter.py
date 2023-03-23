
class GpxExporter:
    
    def __init__(self) -> None:
        self.activities_to_export: dict[str, any] = {}

    def does_activity_exist(self, activity_id: str) -> bool:
        return activity_id in self.activities_to_export
