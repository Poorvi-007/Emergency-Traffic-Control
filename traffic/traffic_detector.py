import cv2
from ultralytics import YOLO


# -----------------------------------
# Traffic detection model
# -----------------------------------

model = YOLO("yolo11n.pt")


# COCO vehicle classes
VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}


latest_traffic = {
    "vehicle_count": 0,
    "cars": 0,
    "motorcycles": 0,
    "buses": 0,
    "trucks": 0,
    "density": "LOW",
    "congestion": 0
}


def detect_traffic(frame):

    global latest_traffic

    results = model.predict(
        source=frame,
        conf=0.30,
        verbose=False
    )

    cars = 0
    motorcycles = 0
    buses = 0
    trucks = 0

    for result in results:

        if result.boxes is None:
            continue

        for box in result.boxes:

            class_id = int(box.cls[0])

            if class_id == 2:
                cars += 1

            elif class_id == 3:
                motorcycles += 1

            elif class_id == 5:
                buses += 1

            elif class_id == 7:
                trucks += 1


    total = (
        cars
        + motorcycles
        + buses
        + trucks
    )


    # -----------------------------------
    # Traffic density
    # -----------------------------------

    if total <= 8:
        density = "LOW"

    elif total <= 20:
        density = "MEDIUM"

    else:
        density = "HIGH"


    # -----------------------------------
    # Congestion prediction
    # -----------------------------------

    congestion = min(
        round((total / 30) * 100, 1),
        100
    )


    latest_traffic = {

        "vehicle_count": total,

        "cars": cars,

        "motorcycles": motorcycles,

        "buses": buses,

        "trucks": trucks,

        "density": density,

        "congestion": congestion
    }


    return results, latest_traffic


def get_latest_traffic():

    return latest_traffic