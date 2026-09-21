# ============================================================
# AUTOMATIC GREEN CORRIDOR ENGINE
# AI-Based Emergency Traffic Management System
# ============================================================

class TrafficEngine:

    def __init__(self):

        self.junctions = {
            "J1": {
                "name": "Junction 1",
                "status": "NORMAL"
            },
            "J2": {
                "name": "Junction 2",
                "status": "NORMAL"
            },
            "J3": {
                "name": "Junction 3",
                "status": "NORMAL"
            },
            "J4": {
                "name": "Junction 4",
                "status": "NORMAL"
            }
        }

        self.last_zone = None
        self.last_route = []


    # ========================================================
    # GET TRAFFIC INFORMATION
    # ========================================================

    def get_traffic_status(self, traffic_data):

        result = {}

        for junction, data in traffic_data.items():

            result[junction] = {
                "vehicles": data.get("vehicles", 0),
                "density": data.get("density", "LOW"),
                "congestion": data.get("congestion", 0),
                "signal": "NORMAL"
            }

        return result


    # ========================================================
    # GREEN CORRIDOR
    # ========================================================

    def create_green_corridor(
        self,
        current_zone,
        route
    ):

        # Default all junctions to RED during emergency
        signals = {
            "J1": "RED",
            "J2": "RED",
            "J3": "RED",
            "J4": "RED"
        }


        # ----------------------------------------------------
        # Validate current zone
        # ----------------------------------------------------

        if current_zone not in signals:

            return {
                "signals": {
                    "J1": "NORMAL",
                    "J2": "NORMAL",
                    "J3": "NORMAL",
                    "J4": "NORMAL"
                },
                "current_zone": "None",
                "next_junction": "None",
                "corridor_active": False
            }


        # ----------------------------------------------------
        # Convert route into list
        # ----------------------------------------------------

        if isinstance(route, str):

            route_list = [
                item.strip()
                for item in route.split("→")
            ]

        elif isinstance(route, list):

            route_list = route

        else:

            route_list = []


        # Keep only valid junctions

        route_list = [
            junction
            for junction in route_list
            if junction in signals
        ]


        self.last_zone = current_zone
        self.last_route = route_list


        # ----------------------------------------------------
        # CURRENT JUNCTION = GREEN
        # ----------------------------------------------------

        signals[current_zone] = "GREEN"


        # ----------------------------------------------------
        # FIND NEXT JUNCTION
        # ----------------------------------------------------

        next_junction = "None"

        if current_zone in route_list:

            current_index = route_list.index(
                current_zone
            )

            if current_index + 1 < len(route_list):

                next_junction = route_list[
                    current_index + 1
                ]

                # Next junction gets YELLOW
                signals[next_junction] = "YELLOW"


        # ----------------------------------------------------
        # IF CURRENT ZONE IS NOT IN ROUTE
        # ----------------------------------------------------

        elif len(route_list) > 0:

            next_junction = route_list[0]

            signals[next_junction] = "YELLOW"


        # ----------------------------------------------------
        # SAVE SIGNAL STATUS
        # ----------------------------------------------------

        for junction in self.junctions:

            self.junctions[junction]["status"] = (
                signals[junction]
            )


        return {
            "signals": signals,
            "current_zone": current_zone,
            "next_junction": next_junction,
            "corridor_active": True,
            "route": route_list
        }


    # ========================================================
    # NORMAL TRAFFIC
    # ========================================================

    def normal_traffic(self):

        signals = {
            "J1": "NORMAL",
            "J2": "NORMAL",
            "J3": "NORMAL",
            "J4": "NORMAL"
        }

        for junction in self.junctions:

            self.junctions[junction]["status"] = "NORMAL"

        self.last_zone = None
        self.last_route = []

        return {
            "signals": signals,
            "current_zone": "None",
            "next_junction": "None",
            "corridor_active": False,
            "route": []
        }


    # ========================================================
    # GET CURRENT SIGNALS
    # ========================================================

    def get_signals(self):

        return {
            junction:
            self.junctions[junction]["status"]
            for junction in self.junctions
        }