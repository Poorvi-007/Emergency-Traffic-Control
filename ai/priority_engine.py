class PriorityEngine:

    def calculate_priority(
        self,
        vehicle_type,
        confidence,
        distance_km,
        traffic_density,
        emergency_level
    ):

        score = 0

        # Vehicle importance
        if vehicle_type == "ambulance":
            score += 30
        elif vehicle_type == "fire truck":
            score += 35
        elif vehicle_type == "police car":
            score += 25

        # AI confidence
        if confidence >= 80:
            score += 25
        elif confidence >= 60:
            score += 20
        elif confidence >= 40:
            score += 10

        # Distance
        if distance_km <= 1:
            score += 20
        elif distance_km <= 3:
            score += 15
        elif distance_km <= 5:
            score += 10

        # Traffic density
        if traffic_density == "HIGH":
            score += 15
        elif traffic_density == "MEDIUM":
            score += 10
        else:
            score += 5

        # Emergency level
        if emergency_level == "CRITICAL":
            score += 10
        elif emergency_level == "HIGH":
            score += 7
        else:
            score += 3

        # Maximum score
        score = min(score, 100)

        # Priority category
        if score >= 75:
            priority = "HIGH PRIORITY"
        elif score >= 50:
            priority = "MEDIUM PRIORITY"
        else:
            priority = "NORMAL"

        return {
            "priority_score": score,
            "priority": priority
        }