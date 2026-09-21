from flask import Flask, render_template, jsonify, Response
from traffic.signal_timing import SignalTimingEngine

from traffic.traffic_engine import TrafficEngine
from ai.emergency_detector_new import (
    detect_emergency,
    get_latest_traffic,
    generate_video
)
from ai.priority_engine import PriorityEngine
from ai.eta_engine import ETAEngine
from ai.route_engine import RouteEngine


app = Flask(__name__)


# -----------------------------
# AI engines
# -----------------------------
traffic_engine = TrafficEngine()
priority_engine = PriorityEngine()
eta_engine = ETAEngine()
route_engine = RouteEngine()
signal_timing_engine = SignalTimingEngine()


# -----------------------------
# Home
# -----------------------------

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# -----------------------------
# Traffic API
# -----------------------------

@app.route("/traffic")
def traffic():

    live_traffic = get_latest_traffic()

    return jsonify({

        "live": live_traffic,

        "prediction": {

            "level":
                live_traffic["density"],

            "score":
                live_traffic["congestion"]

        },

        "junctions":
            live_traffic["zones"]

    })


# -----------------------------
# Emergency API
# -----------------------------

@app.route("/emergency")
def emergency():

    detection = detect_emergency()


    # No emergency
    if not detection["detected"]:

        return jsonify({

            "detected": False,

            "vehicle": "None",

            "confidence": 0,

            "distance": "-",

            "eta": "-",

            "priority": "NORMAL",

            "priority_score": 0,

            "route": "-",

            "route_score": 0,

            "predicted_congestion": 0,

            "route_reason": "",

            "risk": "LOW",

            "green_corridor": False,

            "signals": {

                "J1": "NORMAL",
                "J2": "NORMAL",
                "J3": "NORMAL",
                "J4": "NORMAL"

            }

        })


    # -----------------------------
    # Traffic information
    # -----------------------------

    live_traffic = get_latest_traffic()

    traffic_data = {}

    for junction in ["J1", "J2", "J3", "J4"]:

        zone = live_traffic["zones"][junction]

        traffic_data[junction] = {

            "vehicles":
                zone["vehicles"],

            "density":
                zone["density"],

            "congestion_percentage":
                zone["congestion"],

            "congestion_risk":
                zone["density"]

        }


    densities = [

        traffic_data["J1"]["density"],
        traffic_data["J2"]["density"],
        traffic_data["J3"]["density"],
        traffic_data["J4"]["density"]

    ]


    if "HIGH" in densities:

        overall_density = "HIGH"

    elif "MEDIUM" in densities:

        overall_density = "MEDIUM"

    else:

        overall_density = "LOW"


    # -----------------------------
    # Best route
    # -----------------------------

    route_result = (
        route_engine.find_best_route(
            traffic_data
        )
    )


    distance_km = route_result.get(
        "distance",
        2.4
    )


    junctions = route_result.get(
        "junctions",
        ["J1", "J2", "J3"]
    )


    # -----------------------------
    # Priority
    # -----------------------------

    emergency_level = "HIGH"


    priority_result = (
        priority_engine.calculate_priority(

            detection["vehicle"],

            detection["confidence"],

            distance_km,

            overall_density,

            emergency_level
        )
    )


    # -----------------------------
    # ETA
    # -----------------------------

    eta = eta_engine.calculate_eta(

        distance_km,

        overall_density
    )


    # -----------------------------
    # Green corridor
    # -----------------------------

    corridor = traffic_engine.create_green_corridor(
        detection["zone"],
        junctions
    )

    signals = corridor["signals"]

    next_junction = corridor["next_junction"]


    # -----------------------------
    # AI Signal Timing
    # -----------------------------

    current_zone_data = traffic_data.get(
        detection["zone"],
        {
            "congestion_percentage": 0
        }
    )

    signal_timing = signal_timing_engine.calculate_green_time(
        current_zone_data.get(
            "congestion_percentage",
            0
        ),
        priority_result["priority_score"],
        detection["zone"]
    )


    # -----------------------------
    # Risk
    # -----------------------------

    if overall_density == "HIGH":

        risk = "HIGH"

    elif overall_density == "MEDIUM":

        risk = "MEDIUM"

    else:

        risk = "LOW"


    # -----------------------------
    # Final response
    # -----------------------------

    return jsonify({

        "detected": True,

        "vehicle": detection["vehicle"],

        "confidence": detection["confidence"],

        "distance": f"{distance_km} km",

        "eta": f"{eta} min",

        "priority":
            priority_result["priority"],

        "priority_score":
            priority_result["priority_score"],

        "route":
            " → ".join(junctions),

        "route_score":
            route_result.get(
                "route_score",
                0
            ),

        "predicted_congestion":
            route_result.get(
                "predicted_congestion",
                0
            ),

        "route_reason":
            route_result.get(
                "reason",
                "Route selected by AI"
            ),

        "risk": risk,

        "green_corridor":
            corridor["corridor_active"],

        "current_zone":
            corridor["current_zone"],

        "next_junction":
            next_junction,

        "signals":
            signals,

        "signal_timing":
    signal_timing,

"movement":
    detection.get("movement", "SEARCHING"),

"tracking":
    detection.get("tracking", False)

})


# -----------------------------
# AI Video Feed
# -----------------------------

@app.route("/video_feed")
def video_feed():

    return Response(

        generate_video(),

        mimetype=
        "multipart/x-mixed-replace; boundary=frame"

    )


# -----------------------------
# Start server
# -----------------------------

if __name__ == "__main__":

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True,

        use_reloader=False
    )