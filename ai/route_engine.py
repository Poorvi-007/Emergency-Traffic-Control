class RouteEngine:

    def find_best_route(self, traffic_data):

        routes = {

            "Route A": {
                "junctions": ["J1", "J2", "J3"],
                "distance": 2.4
            },

            "Route B": {
                "junctions": ["J1", "J3", "J4"],
                "distance": 3.1
            },

            "Route C": {
                "junctions": ["J1", "J4", "J3"],
                "distance": 3.5
            }

        }

        best_route = None
        lowest_score = float("inf")

        route_analysis = {}

        for route_name, route in routes.items():

            traffic_score = 0
            congestion_score = 0
            total_congestion = 0

            for junction in route["junctions"]:

                density = traffic_data[junction]["density"]

                congestion = traffic_data[junction].get(
                    "congestion_percentage",
                    0
                )

                total_congestion += congestion

                if density == "HIGH":
                    traffic_score += 30

                elif density == "MEDIUM":
                    traffic_score += 20

                else:
                    traffic_score += 10

                congestion_score += congestion * 0.3

            distance_score = route["distance"] * 5

            total_score = (
                traffic_score
                + distance_score
                + congestion_score
            )

            average_congestion = (
                total_congestion /
                len(route["junctions"])
            )

            route_analysis[route_name] = {
                "distance": route["distance"],
                "traffic_score": traffic_score,
                "congestion": round(
                    average_congestion,
                    1
                ),
                "route_score": round(
                    total_score,
                    1
                )
            }

            if total_score < lowest_score:

                lowest_score = total_score
                best_route = route_name

        selected_route = routes[best_route]

        selected_analysis = route_analysis[best_route]

        if selected_analysis["congestion"] >= 70:
            reason = "Selected despite high congestion because it has the lowest overall route score."

        elif selected_analysis["congestion"] >= 40:
            reason = "Selected because it provides a good balance between distance and traffic."

        else:
            reason = "Selected because it has low predicted congestion and a short travel distance."

        return {

            "route_name": best_route,

            "junctions": selected_route["junctions"],

            "distance": selected_route["distance"],

            "route_score": selected_analysis["route_score"],

            "predicted_congestion":
                selected_analysis["congestion"],

            "reason": reason,

            "all_routes": route_analysis
        }