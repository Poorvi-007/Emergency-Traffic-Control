class EmergencyDecisionEngine:

    def evaluate(
        self,
        vehicle,
        confidence,
        distance_km,
        traffic_density,
        predicted_congestion
    ):
        score = 0

        # Vehicle priority
        vehicle_scores = {
            "ambulance": 40,
            "fire truck": 35,
            "police car": 30
        }

        vehicle_key = vehicle.lower()
        score += vehicle_scores.get(vehicle_key, 20)

        # Detection confidence
        if confidence >= 80:
            score += 20
        elif confidence >= 60:
            score += 15
        else:
            score += 10

        # Distance
        if distance_km <= 1:
            score += 20
        elif distance_km <= 3:
            score += 15
        elif distance_km <= 5:
            score += 10
        else:
            score += 5

        # Traffic density
        density_scores = {
            "HIGH": 15,
            "MEDIUM": 10,
            "LOW": 5
        }

        score += density_scores.get(
            str(traffic_density).upper(),
            5
        )

        # Predicted congestion
        if predicted_congestion >= 70:
            score += 10
        elif predicted_congestion >= 40:
            score += 7
        else:
            score += 3

        # Limit score
        score = min(score, 100)

        # Determine priority
        if score >= 70:
            priority = "HIGH PRIORITY"
            risk = "HIGH"
        elif score >= 45:
            priority = "MEDIUM PRIORITY"
            risk = "MEDIUM"
        else:
            priority = "NORMAL"
            risk = "LOW"

        # Decision explanation
        reasons = []

        if vehicle_key == "ambulance":
            reasons.append("ambulance detected")

        if confidence >= 80:
            reasons.append("high detection confidence")
        elif confidence >= 60:
            reasons.append("reliable detection confidence")

        if distance_km <= 3:
            reasons.append("emergency vehicle is nearby")

        if str(traffic_density).upper() == "HIGH":
            reasons.append("high traffic congestion")
        elif str(traffic_density).upper() == "MEDIUM":
            reasons.append("medium traffic congestion")

        if predicted_congestion >= 40:
            reasons.append("route congestion predicted")

        if reasons:
            explanation = "AI decision based on " + ", ".join(reasons) + "."
        else:
            explanation = "AI decision based on emergency detection data."

        return {
            "priority_score": score,
            "priority": priority,
            "risk": risk,
            "decision": "ACTIVATE GREEN CORRIDOR"
            if score >= 45
            else "MONITOR EMERGENCY",
            "explanation": explanation
        }