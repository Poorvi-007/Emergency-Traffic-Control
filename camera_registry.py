import math
import os
import xml.etree.ElementTree as ET

import requests


# =====================================================
# BENGALURU CCTV CAMERA REGISTRY
# =====================================================

CAMERA_KML_URL = (
    "https://data.opencity.in/dataset/"
    "dbee4e2c-3bb8-43dc-a834-8aa589cf88fc/"
    "resource/"
    "64a4e7d1-701d-4983-a487-283d62bc514b/"
    "download/"
    "244d7d27-6a5b-441c-b787-23cf02a697ec.kml"
)

CAMERA_CACHE_FILE = os.path.join(
    os.path.dirname(__file__),
    "bengaluru_cameras.kml"
)


# =====================================================
# DISTANCE
# =====================================================

def calculate_distance_meters(
    latitude1,
    longitude1,
    latitude2,
    longitude2
):

    earth_radius = 6371000

    lat1 = math.radians(latitude1)
    lat2 = math.radians(latitude2)

    delta_lat = math.radians(
        latitude2 - latitude1
    )

    delta_lon = math.radians(
        longitude2 - longitude1
    )

    a = (
        math.sin(delta_lat / 2) ** 2
        +
        math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return earth_radius * c


# =====================================================
# DOWNLOAD CAMERA REGISTRY
# =====================================================

def download_camera_registry():

    try:

        response = requests.get(
            CAMERA_KML_URL,
            timeout=20
        )

        response.raise_for_status()

        with open(
            CAMERA_CACHE_FILE,
            "wb"
        ) as file:

            file.write(
                response.content
            )

        print(
            "Camera registry downloaded successfully."
        )

        return True

    except Exception as error:

        print(
            "Camera registry download failed:",
            error
        )

        return False


# =====================================================
# LOAD CAMERA REGISTRY
# =====================================================

def load_camera_registry():

    if not os.path.exists(
        CAMERA_CACHE_FILE
    ):

        success = download_camera_registry()

        if not success:
            return []

    try:

        tree = ET.parse(
            CAMERA_CACHE_FILE
        )

        root = tree.getroot()

        cameras = []

        # Find every Placemark
        for placemark in root.iter():

            if not placemark.tag.endswith(
                "Placemark"
            ):
                continue

            # -----------------------------------------
            # CAMERA NAME / ID
            # -----------------------------------------

            camera_name = None

            for element in placemark.iter():

                if element.tag.endswith("Data"):

                    name_attribute = element.attrib.get(
                        "name",
                        ""
                    )

                    if name_attribute == "@id":

                        value_element = None

                        for child in element:

                            if child.tag.endswith(
                                "value"
                            ):

                                value_element = child
                                break

                        if (
                            value_element is not None
                            and value_element.text
                        ):

                            camera_name = (
                                value_element.text.strip()
                            )

                            break

            if not camera_name:
                camera_name = (
                    "Bengaluru CCTV Camera"
                )

            # -----------------------------------------
            # CAMERA COORDINATES
            # -----------------------------------------

            coordinates_element = None

            for element in placemark.iter():

                if element.tag.endswith(
                    "coordinates"
                ):

                    coordinates_element = element
                    break

            if (
                coordinates_element is None
                or not coordinates_element.text
            ):
                continue

            try:

                coordinate_text = (
                    coordinates_element.text.strip()
                )

                # KML format:
                # longitude,latitude,altitude

                first_coordinate = (
                    coordinate_text.split()[0]
                )

                parts = first_coordinate.split(",")

                if len(parts) < 2:
                    continue

                longitude = float(
                    parts[0]
                )

                latitude = float(
                    parts[1]
                )

            except (
                ValueError,
                IndexError
            ):

                continue

            # -----------------------------------------
            # CAMERA INFORMATION
            # -----------------------------------------

            camera_type = "Unknown"
            camera_mount = "Unknown"
            camera_direction = None
            operator = "Unknown"
            surveillance_zone = "Unknown"

            for element in placemark.iter():

                if not element.tag.endswith(
                    "Data"
                ):
                    continue

                data_name = element.attrib.get(
                    "name",
                    ""
                )

                value = None

                for child in element:

                    if child.tag.endswith(
                        "value"
                    ):

                        if child.text:
                            value = child.text.strip()

                        break

                if not value:
                    continue

                if data_name == "camera:type":
                    camera_type = value

                elif data_name == "camera:mount":
                    camera_mount = value

                elif data_name == "camera:direction":
                    camera_direction = value

                elif data_name == "operator":
                    operator = value

                elif data_name == "surveillance:zone":
                    surveillance_zone = value

            cameras.append({
                "name": camera_name,
                "latitude": latitude,
                "longitude": longitude,
                "camera_type": camera_type,
                "camera_mount": camera_mount,
                "camera_direction": camera_direction,
                "operator": operator,
                "zone": surveillance_zone
            })

        print(
            f"Loaded {len(cameras)} cameras from registry."
        )

        return cameras

    except Exception as error:

        print(
            "Camera registry parsing failed:",
            error
        )

        return []


# =====================================================
# FIND CAMERAS WITHIN RADIUS
# =====================================================

def find_nearby_cameras(
    latitude,
    longitude,
    radius_meters=500
):

    cameras = load_camera_registry()

    nearby_cameras = []

    for camera in cameras:

        distance = calculate_distance_meters(
            latitude,
            longitude,
            camera["latitude"],
            camera["longitude"]
        )

        if distance <= radius_meters:

            camera_result = camera.copy()

            camera_result[
                "distance_meters"
            ] = round(
                distance,
                1
            )

            nearby_cameras.append(
                camera_result
            )

    nearby_cameras.sort(
        key=lambda camera:
        camera["distance_meters"]
    )

    return nearby_cameras


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":

    test_latitude = 12.9276303
    test_longitude = 77.620854

    print("Searching for cameras within 500 meters...")
    print()

    nearby_cameras = find_nearby_cameras(
        test_latitude,
        test_longitude,
        radius_meters=500
    )

    if not nearby_cameras:
        print("No cameras found within 500 meters.")
    else:
        print(
            f"Found {len(nearby_cameras)} camera(s) within 500 meters."
        )
        print()

        for camera in nearby_cameras:
            print(
                f"Camera: {camera.get('name', 'Unknown')}"
            )
            print(
                f"Distance: {camera.get('distance_meters', 0):.1f} meters"
            )
            print(
                f"Latitude: {camera.get('latitude')}"
            )
            print(
                f"Longitude: {camera.get('longitude')}"
            )
            print(
                f"Type: {camera.get('camera_type', 'Unknown')}"
            )
            print("-" * 50)