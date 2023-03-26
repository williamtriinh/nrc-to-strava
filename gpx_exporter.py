import polyline

from xml.etree import ElementTree as ET
from xml.etree.ElementTree import ElementTree, Element, SubElement
from datetime import datetime

from nike import NikeApi

# GPX 1.1 schema documentation: https://www.topografix.com/GPX/1/1/

class GpxExporter:
    
    def __init__(self) -> None:
        self.activities_to_export: set[str] = set()

    def does_activity_exist(self, activity_id: str) -> bool:
        return activity_id in self.activities_to_export
    
    def export_activities(self) -> None:
        for activity_id in self.activities_to_export:
            activity = NikeApi.fetch_activity(activity_id)

            root = Element("gpx", attrib={
                "creator": "https://github.com/williamtriinh/nrc-to-strava",
                "version": "1.1",
                "xmlns": "http://www.topografix.com/GPX/1/1",
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xsi:schemaLocation": "http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd",
            })

            metadata = self._metadata_sub_element(root, activity)

            for metric in activity["metrics"]:
                if metric["type"] == "distance":
                    track = self._track_sub_element(root, activity, metric)

            tree = ElementTree(root)
            ET.indent(tree)
            tree.write(f"{activity['start_epoch_ms']}.gpx", xml_declaration=True, encoding="UTF-8")

    def _metadata_sub_element(self, parent: Element, activity: any) -> SubElement:
        metadata = SubElement(parent, "metadata")
        SubElement(metadata, "name").text = activity["tags"]["com.nike.name"]
        SubElement(metadata, "time").text = datetime.utcfromtimestamp(activity["start_epoch_ms"] / 1000).isoformat() + "Z"
        return metadata

    def _track_sub_element(self, parent: Element, activity: any, metric: any) -> SubElement:
        track = SubElement(parent, "trk")
        SubElement(track, "name").text = activity["tags"]["com.nike.name"]
        if ("note" in activity["tags"]):
            SubElement(track, "desc").text = activity["tags"]["note"]

        for polyline_data in activity["polylines"]:
            track_segment = SubElement(track, "trkseg")
            coordinates = polyline.decode(polyline_data["polyline"])
            self._track_point_sub_element(track_segment, coordinates, metric)

        return track
    
    def _track_point_sub_element(self, parent: Element, coordinates: list[tuple[float, float]], metric: any) -> SubElement:
        for index, coordinate in enumerate(coordinates):
            track_point = SubElement(parent, "trkpt", attrib={
                "lat": str(coordinate[0]),
                "lon": str(coordinate[1]),
            })

            SubElement(track_point, "time").text = datetime.utcfromtimestamp(metric["values"][index]["start_epoch_ms"] / 1000).isoformat() + "Z"

