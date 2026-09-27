"""
Public camera feed discovery layer.

This module does NOT assume that every CCTV camera in the
camera registry has a publicly accessible video feed.

It provides a clean structure for verified public feeds:
    - video stream
    - still image
    - unavailable

Feed URLs must be verified public URLs.
No fake or guessed camera URLs are generated.
"""

from math import radians, sin, cos, sqrt, atan2


def calculate_distance_meters(
    latitude1,
    longitude1,
    latitude2,
    longitude2
):
    """
    Calculate distance between two coordinates using Haversine formula.
    """

    earth_radius = 6371000

    lat1 = radians(latitude1)
    lat2 = radians(latitude2)

    delta_lat = radians(latitude2 - latitude1)
    delta_lon = radians(longitude2 - longitude1)

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(delta_lon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return earth_radius * c


def create_feed_record(
    camera,
    feed_url=None,
    feed_type="unavailable",
    source_name="Unknown",
    verified=False
):
    """
    Create a standard camera-feed record.

    feed_type:
        video
        image
        unavailable
    """

    return {
        "camera_name": camera.get(
            "name",
            "Unknown"
        ),

        "latitude": camera.get(
            "latitude"
        ),

        "longitude": camera.get(
            "longitude"
        ),

        "distance_meters": camera.get(
            "distance_meters",
            0
        ),

        "camera_type": camera.get(
            "camera_type",
            "Unknown"
        ),

        "camera_direction": camera.get(
            "camera_direction",
            "Unknown"
        ),

        "feed_url": feed_url,

        "feed_type": feed_type,

        "source_name": source_name,

        "verified": verified
    }


def find_public_feed_for_camera(camera):
    """
    Look for a verified public feed for a camera.

    At this stage the Bengaluru CCTV registry does not provide
    feed URLs, so an unverified camera is returned as unavailable.

    This prevents the system from pretending that a CCTV camera
    has a live feed when no public feed has actually been found.
    """

    return create_feed_record(
        camera=camera,
        feed_url=None,
        feed_type="unavailable",
        source_name="No verified public feed",
        verified=False
    )


def find_public_feeds(cameras):
    """
    Process nearby cameras and return feed information.
    """

    feeds = []

    for camera in cameras:

        feed = find_public_feed_for_camera(
            camera
        )

        feeds.append(feed)

    return feeds


def get_available_feeds(cameras):
    """
    Return only cameras that have a verified public feed.
    """

    feeds = find_public_feeds(
        cameras
    )

    return [
        feed
        for feed in feeds
        if (
            feed.get("verified") is True
            and feed.get("feed_url")
        )
    ]


if __name__ == "__main__":

    test_camera = {
        "name": "Test Camera",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "distance_meters": 100,
        "camera_type": "fixed",
        "camera_direction": "90"
    }

    result = find_public_feed_for_camera(
        test_camera
    )

    print("Camera feed test:")
    print(result)