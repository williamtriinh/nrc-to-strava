from xml.etree import ElementTree as ET
from xml.etree.ElementTree import ElementTree, Element, SubElement
from datetime import datetime

from nike import NikeApi
from helpers import find

# GPX 1.1 schema documentation: https://www.topografix.com/GPX/1/1/

ISO_8601 = "%Y-%m-%dT%H:%M:%SZ"

class GpxExporter:
    
    def __init__(self) -> None:
        self.activities_to_export: set[str] = set()

    def does_activity_exist(self, activity_id: str) -> bool:
        return activity_id in self.activities_to_export
    
    def export_activities(self) -> None:
        for activity_id in self.activities_to_export:
            activity = NikeApi.fetch_activity(activity_id)

            latitudes = find(activity["metrics"], lambda metric : metric["type"]  == "latitude")["values"]
            longitudes = find(activity["metrics"], lambda metric : metric["type"] == "longitude")["values"]

            root = Element("gpx", attrib={
                "creator": "https://github.com/williamtriinh/nrc-to-strava",
                "version": "1.1",
                "xmlns": "http://www.topografix.com/GPX/1/1",
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xsi:schemaLocation": "http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd",
            })

            self._metadata_sub_element(root, activity)
            self._track_sub_element(root, activity, latitudes, longitudes)

            tree = ElementTree(root)
            ET.indent(tree)
            tree.write(f"./exports/{activity['start_epoch_ms']}.gpx", xml_declaration=True, encoding="UTF-8")

    def _metadata_sub_element(self, parent: Element, activity: any) -> SubElement:
        metadata = SubElement(parent, "metadata")
        SubElement(metadata, "name").text = activity["tags"]["com.nike.name"]

        timestamp = datetime.utcfromtimestamp(activity["start_epoch_ms"] / 1000)
        SubElement(metadata, "time").text = timestamp.strftime(ISO_8601)
        return metadata

    def _track_sub_element(self, parent: Element, activity: any, latitudes: any, longitudes: any) -> SubElement:
        track = SubElement(parent, "trk")
        SubElement(track, "name").text = activity["tags"]["com.nike.name"]
        if ("note" in activity["tags"]):
            SubElement(track, "desc").text = activity["tags"]["note"]

        for index, latitude in enumerate(latitudes):
            track_segment = SubElement(track, "trkseg")
            self._track_point_sub_element(track_segment, latitude, longitudes[index])

        return track
    
    def _track_point_sub_element(self, parent: Element, latitude: any, longitude: any) -> SubElement:
            track_point = SubElement(parent, "trkpt", attrib={
                "lat": str(latitude["value"]),
                "lon": str(longitude["value"]),
            })

            timestamp = datetime.utcfromtimestamp(latitude["start_epoch_ms"] / 1000)
            SubElement(track_point, "time").text = timestamp.strftime(ISO_8601)
