class ETAEngine:

    def calculate_eta(self, distance_km, traffic_density):

        # Base average speed in km/h
        if traffic_density == "HIGH":
            speed = 20
        elif traffic_density == "MEDIUM":
            speed = 30
        else:
            speed = 40

        # Calculate time in hours
        time_hours = distance_km / speed

        # Convert hours to minutes
        time_minutes = time_hours * 60

        # Minimum ETA of 1 minute
        time_minutes = max(1, time_minutes)

        return round(time_minutes, 1)