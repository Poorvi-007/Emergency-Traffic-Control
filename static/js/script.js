console.log("Smart Traffic Control System Started");


let emergencyDataReceived = false;

// =====================================================
// GLOBAL VARIABLES
// =====================================================

let signalTimer = null;

let remainingSeconds = 0;

let currentSignalPhase = "GREEN";

let currentTiming = null;

let lastValidEmergencyData =
    JSON.parse(localStorage.getItem("lastEmergencyData")) || null;

let lastValidEmergencyTime = 0;

// Emergency event history
let emergencyHistory = [];

try {
    emergencyHistory =
        JSON.parse(localStorage.getItem("emergencyHistory")) || [];
} catch (error) {
    emergencyHistory = [];
}

let lastEmergencyHistoryKey =
    emergencyHistory.length > 0
        ? emergencyHistory[0].eventKey
        : null;

let emergencyHistoryNoDetectionSince = 0;


// =====================================================
// HELPER
// =====================================================

function setText(id, value) {

    const element = document.getElementById(id);

    if (element) {
        element.textContent = value;
    }
}


// =====================================================
// TRAFFIC DATA
// =====================================================

async function loadTrafficData() {

    console.log("Loading traffic data...");

    try {

        const response =
            await fetch("/traffic?t=" + Date.now());

        if (!response.ok) {
            throw new Error(
                "Traffic API error: " + response.status
            );
        }

        const data =
            await response.json();

        console.log(
            "TRAFFIC DATA RECEIVED:",
            data
        );


        if (!data.live) {
            console.error("No live traffic data");
            return;
        }


        // =================================================
        // OVERALL TRAFFIC
        // =================================================

        setText(
            "trafficDensity",
            data.live.density
        );

        setText(
            "vehicleCount",
            data.live.vehicle_count
        );

        setText(
            "carCount",
            data.live.cars
        );

        setText(
            "motorcycleCount",
            data.live.motorcycles
        );

        setText(
            "busCount",
            data.live.buses
        );

        setText(
            "truckCount",
            data.live.trucks
        );


        // =================================================
        // JUNCTION DATA
        // =================================================

        const zones = data.live.zones;

        if (zones) {

            // J1
            if (zones.J1) {

                setText(
                    "junction1Vehicles",
                    zones.J1.vehicles
                );

                setText(
                    "junction1Density",
                    zones.J1.density
                );

                setText(
                    "junction1Congestion",
                    zones.J1.congestion + "%"
                );
            }


            // J2
            if (zones.J2) {

                setText(
                    "junction2Vehicles",
                    zones.J2.vehicles
                );

                setText(
                    "junction2Density",
                    zones.J2.density
                );

                setText(
                    "junction2Congestion",
                    zones.J2.congestion + "%"
                );
            }


            // J3
            if (zones.J3) {

                setText(
                    "junction3Vehicles",
                    zones.J3.vehicles
                );

                setText(
                    "junction3Density",
                    zones.J3.density
                );

                setText(
                    "junction3Congestion",
                    zones.J3.congestion + "%"
                );
            }


            // J4
            if (zones.J4) {

                setText(
                    "junction4Vehicles",
                    zones.J4.vehicles
                );

                setText(
                    "junction4Density",
                    zones.J4.density
                );

                setText(
                    "junction4Congestion",
                    zones.J4.congestion + "%"
                );
            }
        }


        console.log(
            "TRAFFIC VALUES UPDATED"
        );
        updateAnalytics(data);

    }
    catch (error) {

        console.error(
            "TRAFFIC ERROR:",
            error
        );

    }
}

// =====================================================
// AI ANALYTICS
// =====================================================

function updateAnalytics(trafficData = null) {

    // Emergency event count
    const emergencyEvents =
        Array.isArray(emergencyHistory)
            ? emergencyHistory.length
            : 0;

    setText(
        "analyticsEmergencyEvents",
        emergencyEvents
    );


    // Green corridor count
    let greenCorridors = 0;

    if (Array.isArray(emergencyHistory)) {

        greenCorridors =
            emergencyHistory.filter(function (event) {

                return event.green_corridor === true;

            }).length;
    }

    setText(
        "analyticsGreenCorridors",
        greenCorridors
    );


    // Average ETA
    let totalEta = 0;
    let etaCount = 0;

    if (Array.isArray(emergencyHistory)) {

        emergencyHistory.forEach(function (event) {

            if (!event.eta) {
                return;
            }

            const etaValue =
                parseFloat(
                    String(event.eta)
                );

            if (Number.isFinite(etaValue)) {

                totalEta += etaValue;
                etaCount++;
            }
        });
    }

    if (etaCount > 0) {

        const averageEta =
            totalEta / etaCount;

        setText(
            "analyticsAverageEta",
            averageEta.toFixed(1) + " min"
        );

    } else {

        setText(
            "analyticsAverageEta",
            "-- min"
        );
    }


    // Current traffic congestion
    if (
        trafficData &&
        trafficData.live &&
        trafficData.live.density
    ) {

        setText(
            "analyticsCongestion",
            trafficData.live.density
        );
    }
}

function displayEmergencyData(data) {

    if (!data || !data.detected) {
        return;
    }

    setText("emergencyStatus",
        data.vehicle + " detected — Emergency priority activated");

    setText("vehicle", data.vehicle);
    setText("confidence", Number(data.confidence).toFixed(1) + "%");
    setText("distance", data.distance);
    setText("eta", data.eta);
    setText("priority", data.priority);

    setText(
    "aiDecision",
    data.ai_decision || "AI decision unavailable"
);

setText(
    "aiExplanation",
    data.ai_explanation || "No AI explanation available."
);

    const priorityElement = document.getElementById("priority");

if (priorityElement) {
    priorityElement.classList.remove("high", "medium", "normal");

    const priorityValue = String(data.priority || "NORMAL").toLowerCase();

    if (priorityValue === "high") {
        priorityElement.classList.add("high");
    } else if (priorityValue === "medium") {
        priorityElement.classList.add("medium");
    } else {
        priorityElement.classList.add("normal");
    }
}
    setText("priorityScore", data.priority_score);
    setText("route", data.route);
    setText("risk", data.risk);

    setText("currentZone", data.current_zone || "--");
    setText("movement", data.movement || "--");
    setText("tracking", data.tracking ? "ACTIVE" : "SEARCHING");

    setText(
        "alertMessage",
        "🚑 " + data.vehicle + " detected. Green corridor activated."
    );

    updateSignal("signal1", data.signals?.J1);
    updateSignal("signal2", data.signals?.J2);
    updateSignal("signal3", data.signals?.J3);
    updateSignal("signal4", data.signals?.J4);

    updateRouteVisual(data.signals);

    if (data.signal_timing) {
        setText(
            "timingJunction",
            data.signal_timing.junction || "--"
        );

        setText(
            "nextJunction",
            data.next_junction || "--"
        );

        startSignalCountdown(data.signal_timing);
    }
}

// =========================
// EMERGENCY EVENT HISTORY
// =========================

function escapeHistoryText(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


function renderEmergencyHistory() {

    const container = document.getElementById("emergencyHistory");

    if (!container) {
        return;
    }

    if (emergencyHistory.length === 0) {

        container.innerHTML = `
            <p class="history-empty">
                No emergency events recorded yet.
            </p>
        `;

        return;
    }

    container.innerHTML = emergencyHistory.map(event => `
        <div class="history-item">

            <div class="history-header">

                <div class="history-vehicle">
                    🚑 ${escapeHistoryText(event.vehicle)}
                </div>

                <div class="history-time">
                    ${escapeHistoryText(event.time)}
                </div>

            </div>

            <div class="history-details">

                <div class="history-detail">
                    <span>Confidence</span>
                    <strong>${escapeHistoryText(event.confidence)}%</strong>
                </div>

                <div class="history-detail">
                    <span>Current Zone</span>
                    <strong>${escapeHistoryText(event.currentZone)}</strong>
                </div>

                <div class="history-detail">
                    <span>Next Junction</span>
                    <strong>${escapeHistoryText(event.nextJunction)}</strong>
                </div>

                <div class="history-detail">
                    <span>Priority</span>
                    <strong>${escapeHistoryText(event.priority)}</strong>
                </div>

                <div class="history-detail">
                    <span>ETA</span>
                    <strong>${escapeHistoryText(event.eta)}</strong>
                </div>

                <div class="history-detail">
                    <span>Route</span>
                    <strong>${escapeHistoryText(event.route)}</strong>
                </div>

            </div>

        </div>
    `).join("");
}

function escapeHistoryText(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


function renderEmergencyHistory() {

    const container = document.getElementById("emergencyHistory");

    if (!container) {
        return;
    }

    if (emergencyHistory.length === 0) {
        container.innerHTML = `
            <p class="history-empty">
                No emergency events recorded yet.
            </p>
        `;
        return;
    }

    container.innerHTML = emergencyHistory.map(event => `
        <div class="history-item">

            <div class="history-header">

                <div class="history-vehicle">
                    🚑 ${escapeHistoryText(event.vehicle)}
                </div>

                <div class="history-time">
                    ${escapeHistoryText(event.time)}
                </div>

            </div>

            <div class="history-details">

                <div class="history-detail">
                    <span>Confidence</span>
                    <strong>${escapeHistoryText(event.confidence)}%</strong>
                </div>

                <div class="history-detail">
                    <span>Current Zone</span>
                    <strong>${escapeHistoryText(event.currentZone)}</strong>
                </div>

                <div class="history-detail">
                    <span>Next Junction</span>
                    <strong>${escapeHistoryText(event.nextJunction)}</strong>
                </div>

                <div class="history-detail">
                    <span>Priority</span>
                    <strong>${escapeHistoryText(event.priority)}</strong>
                </div>

                <div class="history-detail">
                    <span>ETA</span>
                    <strong>${escapeHistoryText(event.eta)}</strong>
                </div>

                <div class="history-detail">
                    <span>Route</span>
                    <strong>${escapeHistoryText(event.route)}</strong>
                </div>

            </div>

        </div>
    `).join("");
}


function recordEmergencyEvent(data) {

    if (!data || !data.detected) {
        return;
    }

    const eventKey = [
        data.vehicle || "",
        data.current_zone || "",
        data.next_junction || "",
        data.route || "",
        data.priority || ""
    ].join("|");

    const now = Date.now();

    const longGap =
        emergencyHistoryNoDetectionSince > 0 &&
        (now - emergencyHistoryNoDetectionSince) >= 15000;

    if (
        eventKey === lastEmergencyHistoryKey &&
        !longGap
    ) {
        return;
    }

    const event = {
        eventKey: eventKey,
        vehicle: data.vehicle || "Unknown",
        confidence: Number(data.confidence || 0).toFixed(1),
        currentZone: data.current_zone || "--",
        nextJunction: data.next_junction || "--",
        priority: data.priority || "NORMAL",
        eta: data.eta || "--",
        route: data.route || "--",
        time: new Date().toLocaleTimeString()
    };

    emergencyHistory.unshift(event);

    emergencyHistory = emergencyHistory.slice(0, 10);

    localStorage.setItem(
        "emergencyHistory",
        JSON.stringify(emergencyHistory)
    );

    lastEmergencyHistoryKey = eventKey;
    emergencyHistoryNoDetectionSince = 0;

    renderEmergencyHistory();
}

function recordEmergencyEvent(data) {

    if (!data || !data.detected) {
        return;
    }

    const eventKey = [
        data.vehicle || "",
        data.current_zone || "",
        data.next_junction || "",
        data.route || "",
        data.priority || ""
    ].join("|");

    const now = Date.now();

    /*
       Do not create a new history item every 3 seconds.
       A new event is created only when:
       - the emergency information changes, OR
       - detection has been absent for at least 15 seconds.
    */

    const longGap =
        emergencyHistoryNoDetectionSince > 0 &&
        (now - emergencyHistoryNoDetectionSince) >= 15000;

    if (
        eventKey === lastEmergencyHistoryKey &&
        !longGap
    ) {
        return;
    }

    const event = {
        eventKey: eventKey,
        vehicle: data.vehicle || "Unknown",
        confidence: Number(data.confidence || 0).toFixed(1),
        currentZone: data.current_zone || "--",
        nextJunction: data.next_junction || "--",
        priority: data.priority || "NORMAL",
        eta: data.eta || "--",
        route: data.route || "--",
        time: new Date().toLocaleTimeString()
    };

    emergencyHistory.unshift(event);

    // Keep only the latest 10 events
    emergencyHistory = emergencyHistory.slice(0, 10);

    localStorage.setItem(
        "emergencyHistory",
        JSON.stringify(emergencyHistory)
    );

    lastEmergencyHistoryKey = eventKey;
    emergencyHistoryNoDetectionSince = 0;

    renderEmergencyHistory();
}
// =====================================================
// EMERGENCY DATA
// =====================================================

async function loadEmergencyData() {

    console.log("Loading emergency data...");

    try {

        const response =
            await fetch("/emergency?t=" + Date.now());

        if (!response.ok) {
            throw new Error(
                "Emergency API error: " +
                response.status
            );
        }

        const data =
            await response.json();

        emergencyDataReceived = true;

        console.log(
            "EMERGENCY DATA RECEIVED:",
            data
        );


        // =================================================
        // EMERGENCY DETECTED
        // =================================================

        if (data.detected) {

            // Save latest valid detection
            lastValidEmergencyData = data;
lastValidEmergencyTime = Date.now();

localStorage.setItem("lastEmergencyData", JSON.stringify(data));
recordEmergencyEvent(data);
updateAnalytics(data);


            // =================================================
            // BASIC EMERGENCY INFORMATION
            // =================================================

            setText(
                "emergencyStatus",
                data.vehicle +
                " detected — Emergency priority activated"
            );

            setText(
                "vehicle",
                data.vehicle
            );

            setText(
                "confidence",
                Number(data.confidence).toFixed(1) +
                "%"
            );

            setText(
                "distance",
                data.distance
            );

            setText(
                "eta",
                data.eta
            );

            setText(
                "priority",
                data.priority
            );

            setText(
                "priorityScore",
                data.priority_score
            );

            setText(
                "route",
                data.route
            );

            setText(
                "risk",
                data.risk
            );


            // =================================================
            // LOCATION / MOVEMENT / TRACKING
            // =================================================

            setText(
                "currentZone",
                data.current_zone || "--"
            );

            setText(
                "movement",
                data.movement || "--"
            );

            setText(
                "tracking",
                data.tracking
                    ? "ACTIVE"
                    : "SEARCHING"
            );


            // =================================================
            // ALERT
            // =================================================

            setText(
                "alertMessage",
                "🚑 " +
                data.vehicle +
                " detected. Green corridor activated."
            );


            // =================================================
            // SIGNALS
            // =================================================

            updateSignal(
                "signal1",
                data.signals?.J1
            );

            updateSignal(
                "signal2",
                data.signals?.J2
            );

            updateSignal(
                "signal3",
                data.signals?.J3
            );

            updateSignal(
                "signal4",
                data.signals?.J4
            );


            // =================================================
            // ROUTE VISUAL
            // =================================================

            updateRouteVisual(
                data.signals
            );


            // =================================================
            // SIGNAL TIMING
            // =================================================

            if (data.signal_timing) {

                setText(
                    "timingJunction",
                    data.signal_timing.junction || "--"
                );

                setText(
                    "nextJunction",
                    data.next_junction || "--"
                );


                // Start countdown only once
                startSignalCountdown(
                    data.signal_timing
                );
            }

            return;
        }


        // =================================================
        // NO DETECTION
        // =================================================

        else {
            if (emergencyHistoryNoDetectionSince === 0) {
                emergencyHistoryNoDetectionSince = Date.now();
            }

            console.log("Temporary no-detection result received.");

            // Keep the last valid emergency result.
            // Do NOT clear the dashboard.
            if (lastValidEmergencyData) {
                console.log("Keeping previous emergency data.");
                return;
            }

            console.log(
                "Waiting for first valid emergency detection..."
            );

            return;
        }

    }
    catch (error) {

        console.error(
            "EMERGENCY ERROR:",
            error
        );

    }
}
// =====================================================
// CLEAR EMERGENCY DISPLAY
// =====================================================

function clearEmergencyDisplay() {

    console.log(
        "No emergency detected for 15 seconds."
    );


    setText(
        "emergencyStatus",
        "No emergency vehicle detected"
    );

    setText(
        "vehicle",
        "None"
    );

    setText(
        "confidence",
        "0%"
    );

    setText(
        "distance",
        "-- km"
    );

    setText(
        "eta",
        "-- min"
    );

    setText(
        "priority",
        "NORMAL"
    );

    setText(
        "priorityScore",
        "0"
    );

    setText(
        "route",
        "Not Available"
    );

    setText(
        "risk",
        "LOW"
    );

    setText(
        "currentZone",
        "--"
    );

    setText(
        "movement",
        "--"
    );

    setText(
        "tracking",
        "--"
    );

    setText(
        "alertMessage",
        "No emergency detected. Traffic operating normally."
    );


    setText(
        "timingJunction",
        "--"
    );

    setText(
        "greenTime",
        "--"
    );

    setText(
        "yellowTime",
        "--"
    );

    setText(
        "redTime",
        "--"
    );

    setText(
        "nextJunction",
        "--"
    );


    // NORMAL SIGNALS

    updateSignal(
        "signal1",
        "NORMAL"
    );

    updateSignal(
        "signal2",
        "NORMAL"
    );

    updateSignal(
        "signal3",
        "NORMAL"
    );

    updateSignal(
        "signal4",
        "NORMAL"
    );


    updateRouteVisual({

        J1: "NORMAL",
        J2: "NORMAL",
        J3: "NORMAL",
        J4: "NORMAL"

    });


    stopSignalCountdown();

    lastValidEmergencyTime = 0;
}

// =====================================================
// SIGNALS
// =====================================================

function updateSignal(id, state) {

    const element =
        document.getElementById(id);

    if (!element) {
        return;
    }


    element.classList.remove(
        "green",
        "yellow",
        "red"
    );


    if (state === "GREEN") {

        element.textContent =
            "🟢 GREEN";

        element.classList.add(
            "green"
        );

    }

    else if (state === "YELLOW") {

        element.textContent =
            "🟡 YELLOW";

        element.classList.add(
            "yellow"
        );

    }

    else if (state === "RED") {

        element.textContent =
            "🔴 RED";

        element.classList.add(
            "red"
        );

    }

    else {

        element.textContent =
            "⚪ NORMAL";
    }
}


// =====================================================
// ROUTE VISUAL
// =====================================================
function updateRouteVisual(signals) {

    if (!signals) {
        return;
    }


    const routeSignals = {

        J1: "routeSignal1",
        J2: "routeSignal2",
        J3: "routeSignal3",
        J4: "routeSignal4"

    };


    for (
        const junction in routeSignals
    ) {

        const element =
            document.getElementById(
                routeSignals[junction]
            );

        if (!element) {
            continue;
        }


        const state =
            signals[junction];


        if (state === "GREEN") {

            element.textContent =
                "🟢";

        }

        else if (state === "YELLOW") {

            element.textContent =
                "🟡";

        }

        else if (state === "RED") {

            element.textContent =
                "🔴";

        }

        else {

            element.textContent =
                "⚪";
        }
    }
}


// =====================================================
// SIGNAL COUNTDOWN
// =====================================================

function startSignalCountdown(timing) {

    if (!timing) {
        return;
    }

    const green = Number(timing.green_time);
    const yellow = Number(timing.yellow_time);
    const red = Number(timing.red_time);

    if (
        !Number.isFinite(green) ||
        !Number.isFinite(yellow) ||
        !Number.isFinite(red) ||
        green <= 0 ||
        yellow <= 0 ||
        red <= 0
    ) {
        return;
    }

    // IMPORTANT:
    // If countdown is already running, NEVER restart it.
    if (signalTimer !== null) {
        return;
    }

    currentTiming = {
        green_time: green,
        yellow_time: yellow,
        red_time: red
    };

    currentSignalPhase = "GREEN";

    // Start exactly once at the beginning
    remainingSeconds = green;

    updateCountdownDisplay();

    signalTimer = setInterval(function () {

        remainingSeconds--;

        if (remainingSeconds <= 0) {

            if (currentSignalPhase === "GREEN") {

                currentSignalPhase = "YELLOW";

                remainingSeconds =
                    currentTiming.yellow_time;
            }

            else if (currentSignalPhase === "YELLOW") {

                currentSignalPhase = "RED";

                remainingSeconds =
                    currentTiming.red_time;
            }

            else if (currentSignalPhase === "RED") {

                currentSignalPhase = "GREEN";

                remainingSeconds =
                    currentTiming.green_time;
            }
        }

        updateCountdownDisplay();

    }, 1000);
}


// =====================================================
// COUNTDOWN DISPLAY
// =====================================================

function updateCountdownDisplay() {

    if (!currentTiming) {
        return;
    }

    if (currentSignalPhase === "GREEN") {

        setText(
            "greenTime",
            remainingSeconds + " seconds"
        );

        setText(
            "yellowTime",
            currentTiming.yellow_time + " seconds"
        );

        setText(
            "redTime",
            currentTiming.red_time + " seconds"
        );
    }

    else if (currentSignalPhase === "YELLOW") {

        setText(
            "greenTime",
            "0 seconds"
        );

        setText(
            "yellowTime",
            remainingSeconds + " seconds"
        );

        setText(
            "redTime",
            currentTiming.red_time + " seconds"
        );
    }

    else if (currentSignalPhase === "RED") {

        setText(
            "greenTime",
            "0 seconds"
        );

        setText(
            "yellowTime",
            "0 seconds"
        );

        setText(
            "redTime",
            remainingSeconds + " seconds"
        );
    }
}

// =====================================================
// STOP COUNTDOWN
// =====================================================

function stopSignalCountdown() {

    if (signalTimer !== null) {

        clearInterval(
            signalTimer
        );

        signalTimer = null;
    }


    remainingSeconds = 0;

    currentSignalPhase =
        "GREEN";

    currentTiming = null;
}


// =====================================================
// START SYSTEM
// =====================================================

console.log(
    "Starting traffic monitoring..."
);


loadTrafficData();

renderEmergencyHistory();
updateAnalytics();


if (lastValidEmergencyData) {
    displayEmergencyData(lastValidEmergencyData);
}

loadEmergencyData();




// =====================================================
// AUTO UPDATE
// =====================================================

setInterval(
    loadTrafficData,
    3000
);


setInterval(
    loadEmergencyData,
    3000
);
