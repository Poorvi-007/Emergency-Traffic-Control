from ai.emergency_decision_engine import EmergencyDecisionEngine
from ai.emergency_detector_new import detect_emergency, generate_video, get_latest_traffic
from ai.eta_engine import ETAEngine
from ai.priority_engine import PriorityEngine
from ai.route_engine import RouteEngine
from flask import Flask, Response, jsonify, render_template
from traffic.signal_timing import SignalTimingEngine
from traffic.traffic_engine import TrafficEngine

app = Flask(__name__)

# -----------------------------
# AI engines
# -----------------------------
traffic_engine = TrafficEngine()
priority_engine = PriorityEngine()
eta_engine = ETAEngine()
route_engine = RouteEngine()
signal_timing_engine = SignalTimingEngine()
decision_engine = EmergencyDecisionEngine()


# -----------------------------
# Home
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# Traffic API
# -----------------------------
@app.route("/traffic")
def traffic():
    live_traffic = get_latest_traffic()
    return jsonify({
        "live": live_traffic,
        "prediction": {
            "level": live_traffic.get("density", "LOW"),
            "score": live_traffic.get("congestion", 0)
        },
        "junctions": live_traffic.get("zones", {})
    })


# -----------------------------
# Emergency API
# -----------------------------
@app.route("/emergency")
def emergency():
    detection = detect_emergency()

    if not detection.get("detected", False):
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

    live_traffic = get_latest_traffic()
    zones = live_traffic.get("zones", {})

    traffic_data = {}
    for junction in ["J1", "J2", "J3", "J4"]:
        zone = zones.get(junction, {"vehicles": 0, "density": "LOW", "congestion": 0})
        traffic_data[junction] = {
            "vehicles": zone.get("vehicles", 0),
            "density": zone.get("density", "LOW"),
            "congestion_percentage": zone.get("congestion", 0),
            "congestion_risk": zone.get("density", "LOW")
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

    route_result = route_engine.find_best_route(traffic_data)
    distance_km = route_result.get("distance", 2.4)
    junctions = route_result.get("junctions", ["J1", "J2", "J3"])

    emergency_level = (
        "HIGH" if detection.get("confidence", 0) >= 80
        else "MEDIUM" if detection.get("confidence", 0) >= 60
        else "LOW"
    )

    priority_result = priority_engine.calculate_priority(
        detection["vehicle"].lower(),
        detection.get("confidence", 0),
        distance_km,
        overall_density,
        emergency_level,
    )

    decision_result = decision_engine.evaluate(
        detection["vehicle"],
        detection.get("confidence", 0),
        distance_km,
        overall_density,
        route_result.get("predicted_congestion", 0)
    )

    eta = eta_engine.calculate_eta(distance_km, overall_density)

    corridor = traffic_engine.create_green_corridor(detection.get("zone", "J1"), junctions)
    signals = corridor["signals"]
    next_junction = corridor["next_junction"]

    current_zone_data = traffic_data.get(detection.get("zone", "J1"), {"congestion_percentage": 0})
    signal_timing = signal_timing_engine.calculate_green_time(
        current_zone_data.get("congestion_percentage", 0),
        priority_result["priority_score"],
        detection.get("zone", "J1")
    )

    if overall_density == "HIGH":
        risk = "HIGH"
    elif overall_density == "MEDIUM":
        risk = "MEDIUM"
    else:
        risk = "LOW"

    return jsonify({
        "detected": True,
        "vehicle": detection["vehicle"],
        "confidence": detection.get("confidence", 0),
        "distance": f"{distance_km} km",
        "eta": f"{eta} min",
        "priority": priority_result["priority"],
        "priority_score": priority_result["priority_score"],
        "route": " → ".join(junctions),
        "route_score": route_result.get("route_score", 0),
        "predicted_congestion": route_result.get("predicted_congestion", 0),
        "route_reason": route_result.get("reason", "Route selected by AI"),
        "risk": risk,
        "green_corridor": corridor["corridor_active"],
        "current_zone": corridor["current_zone"],
        "next_junction": next_junction,
        "signals": signals,
        "signal_timing": signal_timing,
        "movement": detection.get("movement", "SEARCHING"),
        "tracking": detection.get("tracking", False),
        "ai_decision": decision_result["decision"],
        "ai_explanation": decision_result["explanation"]
    })


# -----------------------------
# AI Video Feed
# -----------------------------
@app.route("/video_feed")
def video_feed():
    return Response(
        generate_video(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
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