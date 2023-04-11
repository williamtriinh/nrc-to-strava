from fit_tool.fit_file_builder import FitFileBuilder
from fit_tool.profile.messages.activity_message import ActivityMessage
from fit_tool.profile.messages.course_message import CourseMessage
from fit_tool.profile.messages.event_message import EventMessage
from fit_tool.profile.messages.file_id_message import FileIdMessage
from fit_tool.profile.messages.lap_message import LapMessage
from fit_tool.profile.messages.record_message import RecordMessage
from fit_tool.profile.messages.session_message import SessionMessage
from fit_tool.profile.profile_type import Event, EventType, FileType, Manufacturer, Sport
from datetime import datetime
from geopy.distance import geodesic
import math

from nike import NikeApi
from helpers import find

# https://developer.garmin.com/fit/protocol/
# https://developer.garmin.com/fit/file-types/activity/

class FitExporter:
    def export_activities(self, activity_ids) -> None:
        for activity_id in activity_ids:
            activity = NikeApi.fetch_activity(activity_id)

            summaries: dict[str, any] = {
                "ascent": find(activity["summaries"], lambda metric : metric["metric"] == "ascent"),
                "distance": find(activity["summaries"], lambda metric : metric["metric"] == "distance"),
            }

            metrics: dict[str, any] = {
                "elevation": find(activity["metrics"], lambda metric : metric["type"] == "elevation")["values"],
                "latitude": find(activity["metrics"], lambda metric : metric["type"]  == "latitude")["values"],
                "longitude": find(activity["metrics"], lambda metric : metric["type"] == "longitude")["values"],
            }

            builder = FitFileBuilder(auto_define = True)

            # Creates a File Id Message which is used to identify the purpose of the FIT
            # file via the "type" field. This message should be the first message in the
            # file.
            message = FileIdMessage()
            message.manufacturer = Manufacturer.DEVELOPMENT.value
            message.product = 0
            message.time_created = activity["start_epoch_ms"]
            message.type = FileType.ACTIVITY # https://developer.garmin.com/fit/file-types/course/
            builder.add(message)

            # Session message
            message = SessionMessage()
            message.sport = Sport.RUNNING.value
            message.total_ascent = summaries["ascent"]["value"]
            message.total_distance = summaries["distance"]["value"] * 100
            message.total_elapsed_time = activity["active_duration_ms"]
            builder.add(message)

            # Lap message provides summary data associated with the course
            for moment in activity["moments"]:
                if moment["key"] == "split_km":
                    message = LapMessage()
                    message.start_time = moment["timestamp"]
                    message.timestamp = moment["timestamp"]
                    builder.add(message)

            # Event message used to indicate the start of the course
            message = EventMessage()
            message.timestamp = activity["start_epoch_ms"]
            message.event = Event.TIMER
            message.event_type = EventType.START
            builder.add(message)

            # Record messages contain info that define the course
            total_distance = 0
            previous_coordinate: tuple[float, float] | None = None

            for index in range(len(metrics["latitude"])):
                latitude = metrics["latitude"][index]
                longitude = metrics["longitude"][index]
                coordinate = (latitude["value"], longitude["value"])

                distance = 0
                if previous_coordinate:
                    distance = geodesic(previous_coordinate, coordinate).meters
                total_distance += distance
                previous_coordinate = coordinate

                message = RecordMessage()
                message.timestamp = latitude["start_epoch_ms"]
                message.distance = total_distance
                message.position_lat = latitude["value"]
                message.position_long = longitude["value"]
                builder.add(message)

            # Event message used to indicate the end of the course
            message = EventMessage()
            message.timestamp = activity["end_epoch_ms"]
            message.event = Event.TIMER
            message.event_type = EventType.STOP_DISABLE_ALL
            builder.add(message)

            fit_file = builder.build()
            fit_file.to_file(f"./exports/{activity['start_epoch_ms']}.fit")
