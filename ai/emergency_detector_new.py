import os
import cv2

from ultralytics import YOLOE, YOLO


# =====================================================
# VIDEO PATH
# =====================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

VIDEO_PATH = os.path.join(
    BASE_DIR,
    "test_video.mp4"
)


# =====================================================
# AI MODELS
# =====================================================

emergency_model = YOLOE("yoloe-26s-seg.pt")

emergency_model.set_classes([
    "ambulance",
    "fire truck",
    "police car"
])

traffic_model = YOLO("yolo11n.pt")


# =====================================================
# LATEST EMERGENCY DATA
# =====================================================

latest_detection = {
    "detected": False,
    "vehicle": "None",
    "confidence": 0,
    "zone": "None",
    "next_junction": "None",
    "track_id": "EV-01",
    "center_x": 0,
    "center_y": 0,
    "movement": "SEARCHING",
    "tracking": False,
    "track_points": []
}


# =====================================================
# LATEST TRAFFIC DATA
# =====================================================

latest_traffic = {

    "vehicle_count": 0,

    "cars": 0,

    "motorcycles": 0,

    "buses": 0,

    "trucks": 0,

    "density": "LOW",

    "congestion": 0,

    "zones": {

        "J1": {
            "vehicles": 0,
            "density": "LOW",
            "congestion": 0
        },

        "J2": {
            "vehicles": 0,
            "density": "LOW",
            "congestion": 0
        },

        "J3": {
            "vehicles": 0,
            "density": "LOW",
            "congestion": 0
        },

        "J4": {
            "vehicles": 0,
            "density": "LOW",
            "congestion": 0
        }
    }
}


# =====================================================
# VIDEO
# =====================================================

cap = cv2.VideoCapture(
    VIDEO_PATH
)


# =====================================================
# EMERGENCY MEMORY
# =====================================================

missed_emergency_frames = 0

MAX_MISSED_EMERGENCY_FRAMES = 15


# =====================================================
# EMERGENCY TRACKING
# =====================================================

emergency_track_id = "EV-01"

last_emergency_center = None

emergency_track_history = []

emergency_frame_number = 0

MAX_TRACK_HISTORY = 30


# =====================================================
# ZONE ORDER
# =====================================================

ZONE_ORDER = {

    "J1": 1,

    "J2": 2,

    "J3": 3,

    "J4": 4
}


# =====================================================
# FIND ZONE
# =====================================================

def get_zone(center_y, frame_height):

    position = center_y / frame_height

    if position < 0.30:

        return "J1"

    elif position < 0.50:

        return "J2"

    elif position < 0.70:

        return "J3"

    else:

        return "J4"


# =====================================================
# NEXT JUNCTION PREDICTION
# =====================================================

def get_next_junction(current_zone, movement):

    if current_zone == "J1":

        return "J2"

    elif current_zone == "J2":

        return "J3"

    elif current_zone == "J3":

        return "J4"

    elif current_zone == "J4":

        return "None"

    return "None"


# =====================================================
# DENSITY
# =====================================================

def calculate_density(count):

    if count <= 3:

        return "LOW"

    elif count <= 7:

        return "MEDIUM"

    else:

        return "HIGH"


# =====================================================
# CONGESTION
# =====================================================

def calculate_congestion(count):

    return min(

        round(
            (count / 10) * 100,
            1
        ),

        100
    )


# =====================================================
# PROCESS FRAME
# =====================================================

def process_frame(frame):

    global latest_detection

    global latest_traffic

    global missed_emergency_frames

    global last_emergency_center

    global emergency_track_history

    global emergency_frame_number


    frame_height, frame_width = frame.shape[:2]


    # =================================================
    # EMERGENCY DETECTION
    # =================================================

    emergency_results = emergency_model.predict(

        source=frame,

        conf=0.25,

        verbose=False
    )


    best_vehicle = "None"

    best_confidence = 0

    best_zone = "None"

    best_x1 = 0

    best_y1 = 0

    best_x2 = 0

    best_y2 = 0

    emergency_found = False


    # =================================================
    # FIND BEST EMERGENCY VEHICLE
    # =================================================

    for result in emergency_results:

        if result.boxes is None:

            continue


        for box in result.boxes:

            class_id = int(
                box.cls[0]
            )

            confidence = float(
                box.conf[0]
            )

            vehicle = emergency_model.names[
                class_id
            ]


            x1, y1, x2, y2 = (

                box.xyxy[0].tolist()

            )


            center_y = (

                y1 + y2

            ) / 2


            zone = get_zone(

                center_y,

                frame_height

            )


            if confidence > best_confidence:

                best_confidence = confidence

                best_vehicle = vehicle

                best_zone = zone

                best_x1 = x1

                best_y1 = y1

                best_x2 = x2

                best_y2 = y2

                emergency_found = True


    # =================================================
    # UPDATE EMERGENCY + TRACKING
    # =================================================

    emergency_frame_number += 1

    if emergency_found:

        center_x = (best_x1 + best_x2) / 2
        center_y = (best_y1 + best_y2) / 2
        current_zone = get_zone(center_y, frame_height)

        movement = "STATIONARY"

        emergency_track_history.append({
            "x": round(center_x, 1),
            "y": round(center_y, 1),
            "zone": current_zone
        })

        if len(emergency_track_history) > MAX_TRACK_HISTORY:
            emergency_track_history.pop(0)

        if len(emergency_track_history) >= 5:
            old_point = emergency_track_history[-5]
            dx = center_x - old_point["x"]
            dy = center_y - old_point["y"]

            if abs(dx) >= abs(dy):
                if dx > 2:
                    movement = "MOVING RIGHT"
                elif dx < -2:
                    movement = "MOVING LEFT"
                else:
                    movement = "STATIONARY"
            else:
                if dy > 2:
                    movement = "MOVING DOWN"
                elif dy < -2:
                    movement = "MOVING UP"
                else:
                    movement = "STATIONARY"
        else:
            movement = "SEARCHING"

        last_emergency_center = (center_x, center_y)
        next_junction = get_next_junction(current_zone, movement)

        latest_detection = {
            "detected": True,
            "vehicle": best_vehicle,
            "confidence": round(best_confidence * 100, 1),
            "zone": current_zone,
            "next_junction": next_junction,
            "track_id": emergency_track_id,
            "center_x": round(center_x, 1),
"center_y": round(center_y, 1),
"box": [
    int(best_x1),
    int(best_y1),
    int(best_x2),
    int(best_y2)
],
"movement": movement,
            "tracking": True,
            "track_points": emergency_track_history.copy()
        }

        missed_emergency_frames = 0

    else:
        missed_emergency_frames += 1

        if (
            missed_emergency_frames <= MAX_MISSED_EMERGENCY_FRAMES
            and latest_detection.get("detected", False)
        ):
            latest_detection = {
                "detected": True,
                "vehicle": latest_detection.get("vehicle", "None"),
                "confidence": latest_detection.get("confidence", 0),
                "zone": latest_detection.get("zone", "None"),
                "next_junction": latest_detection.get("next_junction", "None"),
                "track_id": emergency_track_id,
                "center_x": latest_detection.get("center_x", 0),
                "center_y": latest_detection.get("center_y", 0),
                "movement": latest_detection.get("movement", "SEARCHING"),
                "tracking": True,
                "track_points": emergency_track_history.copy()
            }

        elif missed_emergency_frames > MAX_MISSED_EMERGENCY_FRAMES:
            latest_detection = {
                "detected": False,
                "vehicle": "None",
                "confidence": 0,
                "zone": "None",
                "next_junction": "None",
                "track_id": emergency_track_id,
                "center_x": 0,
                "center_y": 0,
                "movement": "SEARCHING",
                "tracking": False,
                "track_points": []
            }

            last_emergency_center = None
            emergency_track_history = []


    # =================================================
    # TRAFFIC DETECTION
    # =================================================

    traffic_results = traffic_model.predict(

        source=frame,

        conf=0.30,

        verbose=False
    )


    cars = 0

    motorcycles = 0

    buses = 0

    trucks = 0


    zone_counts = {

        "J1": 0,

        "J2": 0,

        "J3": 0,

        "J4": 0

    }


    # =================================================
    # COUNT VEHICLES
    # =================================================

    for result in traffic_results:

        if result.boxes is None:

            continue


        for box in result.boxes:

            class_id = int(
                box.cls[0]
            )


            x1, y1, x2, y2 = (

                box.xyxy[0].tolist()

            )


            center_y = (

                y1 + y2

            ) / 2


            zone = get_zone(

                center_y,

                frame_height

            )


            if class_id == 2:

                cars += 1

                zone_counts[zone] += 1


            elif class_id == 3:

                motorcycles += 1

                zone_counts[zone] += 1


            elif class_id == 5:

                buses += 1

                zone_counts[zone] += 1


            elif class_id == 7:

                trucks += 1

                zone_counts[zone] += 1


    # =================================================
    # TOTAL
    # =================================================

    total_vehicles = (

        cars
        + motorcycles
        + buses
        + trucks

    )


    overall_density = calculate_density(

        total_vehicles

    )


    overall_congestion = calculate_congestion(

        total_vehicles

    )


    # =================================================
    # ZONES
    # =================================================

    zones = {}


    for junction in [

        "J1",

        "J2",

        "J3",

        "J4"

    ]:

        count = zone_counts[junction]


        zones[junction] = {

            "vehicles": count,

            "density":
                calculate_density(
                    count
                ),

            "congestion":
                calculate_congestion(
                    count
                )

        }


    # =================================================
    # SAVE TRAFFIC
    # =================================================

    latest_traffic = {

        "vehicle_count":
            total_vehicles,

        "cars":
            cars,

        "motorcycles":
            motorcycles,

        "buses":
            buses,

        "trucks":
            trucks,

        "density":
            overall_density,

        "congestion":
            overall_congestion,

        "zones":
            zones

    }


    # =================================================
    # RETURN
    # =================================================

    return (

        emergency_results,

        traffic_results,

        latest_detection,

        latest_traffic

    )


# =====================================================
# GET EMERGENCY
# =====================================================

# =====================================================
# GET EMERGENCY
# =====================================================

def detect_emergency():

    # Return the latest detection produced by
    # the live video processing pipeline.

    return latest_detection.copy()
# =====================================================
# GET TRAFFIC
# =====================================================

def get_latest_traffic():

    return latest_traffic


# =====================================================
# VIDEO STREAM
# =====================================================

def generate_video():

    global cap


    while True:

        if not cap.isOpened():

            cap = cv2.VideoCapture(

                VIDEO_PATH

            )


        success, frame = cap.read()


        if not success:

            cap.release()

            cap = cv2.VideoCapture(

                VIDEO_PATH

            )

            continue


        (

            emergency_results,

            traffic_results,

            detection,

            traffic

        ) = process_frame(frame)


        # =================================================
        # TRAFFIC BOXES
        # =================================================

        if len(traffic_results) > 0:

            frame = traffic_results[0].plot(

                img=frame

            )


        # =================================================
        # ZONE LINES
        # =================================================

        height = frame.shape[0]

        width = frame.shape[1]


        boundaries = [

            (0.30, "J1"),

            (0.50, "J2"),

            (0.70, "J3")

        ]


        for position, name in boundaries:

            y = int(

                position * height

            )


            cv2.line(

                frame,

                (0, y),

                (width, y),

                (255, 255, 0),

                2

            )


            cv2.putText(

                frame,

                name,

                (20, y - 10),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.8,

                (255, 255, 0),

                2

            )


        # =================================================
        # EMERGENCY INFORMATION
        # =================================================

        if detection["detected"]:

            # Draw emergency vehicle bounding box
            box = detection.get("box")

            if box:
                x1, y1, x2, y2 = box

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 0, 255),
                    3
                )

                label = (
                    f'{detection.get("vehicle", "Emergency")} '
                    f'{detection.get("confidence", 0):.1f}%'
                )

                cv2.putText(
                    frame,
                    label,
                    (x1, max(y1 - 10, 25)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2
                )

            emergency_text = (
                f'EMERGENCY: '
                f'{detection["vehicle"]} | '
                f'Confidence: '
                f'{detection["confidence"]}% | '
                f'Zone: '
                f'{detection["zone"]} | '
                f'Next: '
                f'{detection.get("next_junction", "None")}'
            )

        else:

            emergency_text = (
                "EMERGENCY: Searching..."
            )


        cv2.putText(

            frame,

            emergency_text,

            (25, 40),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.75,

            (0, 255, 0),

            2,

            cv2.LINE_AA

        )


        # =================================================
        # REAL-TIME TRACKING OVERLAY
        # =================================================

        if detection["detected"]:

            track_text = (

                f'Tracking: '
                f'{detection["track_id"]} | '

                f'Movement: '
                f'{detection["movement"]}'

            )


            cv2.putText(

                frame,

                track_text,

                (25, 155),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.7,

                (0, 255, 255),

                2,

                cv2.LINE_AA

            )


            # =================================================
            # TRACKING TRAIL
            # =================================================

            points = detection.get(

                "track_points",

                []

            )


            for i in range(

                1,

                len(points)

            ):

                p1 = (

                    int(
                        points[i - 1]["x"]
                    ),

                    int(
                        points[i - 1]["y"]
                    )

                )


                p2 = (

                    int(
                        points[i]["x"]
                    ),

                    int(
                        points[i]["y"]
                    )

                )


                cv2.line(

                    frame,

                    p1,

                    p2,

                    (0, 255, 255),

                    3

                )


            # =================================================
            # CURRENT TRACKED POSITION
            # =================================================

            center = (

                int(
                    detection["center_x"]
                ),

                int(
                    detection["center_y"]
                )

            )


            cv2.circle(

                frame,

                center,

                12,

                (0, 255, 255),

                3

            )


            cv2.putText(

                frame,

                detection["track_id"],

                (

                    center[0] + 15,

                    center[1] - 15

                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.65,

                (0, 255, 255),

                2,

                cv2.LINE_AA

            )


        # =================================================
        # TRAFFIC INFORMATION
        # =================================================

        traffic_text = (

            f'Traffic: '

            f'{traffic["vehicle_count"]} | '

            f'Density: '

            f'{traffic["density"]} | '

            f'Congestion: '

            f'{traffic["congestion"]}%'

        )


        cv2.putText(

            frame,

            traffic_text,

            (25, 80),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.75,

            (255, 255, 0),

            2,

            cv2.LINE_AA

        )


        # =================================================
        # ZONE COUNTS
        # =================================================

        zone_text = (

            f'J1: '
            f'{traffic["zones"]["J1"]["vehicles"]} | '

            f'J2: '
            f'{traffic["zones"]["J2"]["vehicles"]} | '

            f'J3: '
            f'{traffic["zones"]["J3"]["vehicles"]} | '

            f'J4: '
            f'{traffic["zones"]["J4"]["vehicles"]}'

        )


        cv2.putText(

            frame,

            zone_text,

            (25, 120),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.7,

            (255, 255, 255),

            2,

            cv2.LINE_AA

        )


        # =================================================
        # ENCODE
        # =================================================

        success, buffer = cv2.imencode(

            ".jpg",

            frame

        )


        if not success:

            continue


        frame_bytes = buffer.tobytes()


        yield (

            b"--frame\r\n"

            b"Content-Type: image/jpeg\r\n\r\n"

            + frame_bytes

            + b"\r\n"

        )