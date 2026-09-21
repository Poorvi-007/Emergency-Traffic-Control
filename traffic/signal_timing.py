# ============================================================
# AI SIGNAL TIMING ENGINE
# ============================================================

class SignalTimingEngine:

    def calculate_green_time(
        self,
        congestion,
        priority_score,
        current_zone
    ):

        # Base green time
        green_time = 30

        # Traffic congestion
        if congestion >= 70:
            green_time += 20

        elif congestion >= 40:
            green_time += 10

        # Emergency priority
        if priority_score >= 80:
            green_time += 15

        elif priority_score >= 60:
            green_time += 10

        # Keep timing within safe limits
        green_time = max(
            20,
            min(green_time, 90)
        )

        return {
            "junction": current_zone,
            "green_time": green_time,
            "yellow_time": 5,
            "red_time": max(
                10,
                60 - green_time
            )
        }