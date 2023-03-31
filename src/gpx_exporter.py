from xml.etree import ElementTree as ET
from xml.etree.ElementTree import ElementTree, Element, SubElement
from datetime import datetime

from nike import NikeApi
from helpers import find

# GPX 1.1 schema documentation: https://www.topografix.com/GPX/1/1/

ISO_8601 = "%Y-%m-%dT%H:%M:%SZ"

class GpxExporter:
    def export_activities(self, activity_ids) -> None:
        for activity_id in activity_ids:
            activity = NikeApi.fetch_activity(activity_id)

            data: dict[str, any] = {
                "latitude": find(activity["metrics"], lambda metric : metric["type"]  == "latitude")["values"],
                "longitude": find(activity["metrics"], lambda metric : metric["type"] == "longitude")["values"],
                "elevation": find(activity["metrics"], lambda metric : metric["type"] == "elevation")["values"],
            }

            root = Element("gpx", attrib={
                "creator": "https://github.com/williamtriinh/nrc-to-strava",
                "version": "1.1",
                "xmlns": "http://www.topografix.com/GPX/1/1",
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xsi:schemaLocation": "http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd",
            })

            self._metadata_sub_element(root, activity)
            self._track_sub_element(root, activity, data)

            tree = ElementTree(root)
            ET.indent(tree)
            tree.write(f"./exports/{activity['start_epoch_ms']}.gpx", xml_declaration=True, encoding="UTF-8")

    def _metadata_sub_element(self, parent: Element, activity: any) -> SubElement:
        metadata = SubElement(parent, "metadata")

        timestamp = datetime.utcfromtimestamp(activity["start_epoch_ms"] / 1000)
        SubElement(metadata, "time").text = timestamp.strftime(ISO_8601)

        return metadata

    def _track_sub_element(self, parent: Element, activity: any, data: dict[str, any]) -> SubElement:
        track = SubElement(parent, "trk")
        SubElement(track, "name").text = activity["tags"]["com.nike.name"]
        SubElement(track, "cmt").text = f"Nike activity ID: {activity['id']}"

        track_segment = SubElement(track, "trkseg")

        for index, latitude in enumerate(data["latitude"]):
            point_data: dict[str, any] = {
                "latitude": latitude,
                "longitude": data["longitude"][index],
                # There's a chance that elevation data might be missing.
                "elevation": data["elevation"][min(index, len(data["elevation"]) - 1)],
            }
            self._track_point_sub_element(track_segment, point_data)

        return track
    
    def _track_point_sub_element(self, parent: Element, data: dict[str, any]) -> SubElement:
            track_point = SubElement(parent, "trkpt", attrib={
                "lat": str(data["latitude"]["value"]),
                "lon": str(data["longitude"]["value"]),
            })

            SubElement(track_point, "ele").text = str(data["elevation"]["value"])

            timestamp = datetime.utcfromtimestamp(data["latitude"]["start_epoch_ms"] / 1000)
            SubElement(track_point, "time").text = timestamp.strftime(ISO_8601)
