# Robovac — 3D-Printed Mapping Vacuum (LiDAR + Camera SLAM, Server-Backed)

> Design plan and milestone roadmap. Code scaffold lives in the repo root; see
> the top-level [README](../README.md) for a quickstart.

## Context

We're building a **3D-printed robot vacuum from scratch** that:
- Maps the house with a **2D LiDAR** + a **camera** (onboard SLAM).
- **Uploads the map to a server** that stores the house layout, shows a live dashboard, and computes cleaning paths.
- **Localizes itself** ("GPS-like, but from the camera + LiDAR") so it always knows where it is on the map and can plan custom cleaning paths.

The builder is **new to robotics**, chose a **custom Python stack** (not ROS), wants **SLAM to run onboard** with the **server for storage + planning**, and is targeting a **Radxa ROCK 4C+ (RK3399-T, 4GB)** as the robot's brain.

Goal of this plan: a hardware shopping list, a software architecture, and a **beginner-friendly milestone roadmap** where each step produces something you can see working before moving on.

---

## Hardware verdict: will the ROCK 4C+ work? → Yes, with caveats

| Aspect | Verdict |
|---|---|
| CPU (2×A72 @1.5GHz + 4×A53 @1GHz) | ✅ Plenty for **2D LiDAR SLAM** in Python (Pi-4 class). |
| RAM (4GB) | ✅ Fine for 2D occupancy-grid maps + a modest visual DB. |
| GPU (Mali-T860) | ⚠️ Weak for vision. Do **classic OpenCV (ORB features)**, not deep visual SLAM. |
| OS images | ⚠️ Official images are old (Debian 10 / Ubuntu 18.04 → Python 3.6/3.7). **Use the newest Radxa Debian 11/12 image and run everything in a Python venv or Docker** to get a modern Python. |
| Real-time motor/encoder control | ⚠️ Don't do PWM + encoder counting on the SBC. **Offload to an ESP32/Arduino** over USB serial. |

**Bottom line:** good choice for the price. Keep heavy vision classic (no neural nets on-board), and pair it with a microcontroller for motors.

---

## Bill of Materials (recommended starting set)

| Part | Recommendation | ~USD | Notes |
|---|---|---|---|
| Brain (SBC) | **ROCK 4C+ 4GB** (already chosen) | — | Use newest Radxa Debian image. |
| LiDAR | **RPLidar A1** (12 m, 360°, USB) | ~$99 | Best Python-library support (`rplidar` + BreezySLAM examples target it). C1 (~$69) is cheaper/newer TOF but less battle-tested with these libs; A2 (~$229) is overkill. |
| Camera | **USB webcam** (start) → MIPI-CSI cam later | ~$15–40 | USB is easiest for a beginner; CSI frees a USB port later. |
| Motor controller MCU | **ESP32 devkit** | ~$8 | Reads encoders + IMU, drives motors, talks USB-serial to the SBC. |
| Drive motors | **2× DC gear motors w/ quadrature encoders** | ~$25 | Differential drive (2 driven wheels + 1–2 casters). Encoders = odometry. |
| Motor driver | **TB6612FNG** (drive) + small driver for vacuum/brush | ~$10 | TB6612 > L298N (efficiency). |
| IMU | **BNO055** (preferred) or MPU6050 | ~$10–30 | Heading/yaw to fuse with encoder odometry. |
| Safety sensors | IR cliff sensors ×3, bumper microswitches ×2 | ~$10 | Stairs + collision. |
| Suction | Brushless blower fan + roller brush motor | ~$20 | The actual "vacuum." |
| Power | Li-ion pack (3S/4S) + BMS + buck converters (5V/3.3V) | ~$40 | One regulated 5V rail for SBC; separate motor rail. |
| Chassis | **3D-printed** (your part) | — | Mount LiDAR on top, unobstructed 360°; camera forward-facing. |

> If you already own any of these, skip them — this is a from-zero list.

---

## System architecture

```
        ROBOT (ROCK 4C+, Python)                         SERVER (PC / always-on box)
 ┌─────────────────────────────────────┐         ┌──────────────────────────────────────┐
 │ lidar_driver  ── scans ──┐           │         │  FastAPI app                          │
 │ camera        ── frames ─┤           │  HTTP   │   • map store (SQLite + files)        │
 │ odometry  (ESP32 serial) ┤           │ upload  │   • visual keyframe DB                │
 │   encoders + IMU         │           │ ───────▶│   • coverage/path planner (server)    │
 │            ▼             │           │         │   • REST API (rooms, no-go zones)     │
 │   SLAM (BreezySLAM) ─► occupancy grid│         │                                       │
 │            +            │           │  MQTT   │  Mosquitto broker                     │
 │   visual localization ──► global pose│◀──────▶ │   • live pose / status telemetry      │
 │            ▼             │  realtime │         │                                       │
 │   navigation (A* + coverage) ────────┤         │  Web dashboard (HTML+canvas/JS)       │
 │            ▼             │           │  WS     │   • live map + robot dot              │
 │   motion_control ─► ESP32 ─► motors  │◀──────▶ │   • start/stop, pick room             │
 └─────────────────────────────────────┘         └──────────────────────────────────────┘
```

**Why this split:** SLAM + obstacle avoidance run **onboard** so navigation never depends on Wi-Fi latency. The server handles the non-latency-critical, "remembered" stuff: storing the house map, the dashboard, and high-level cleaning plans the robot then executes locally.

---

## The "GPS from cameras" design (important)

Real robovacs localize primarily with **LiDAR**, and so will we — it's reliable and beginner-achievable. The camera is the **secondary "visual GPS"** layer:

1. **Backbone localization = LiDAR.** BreezySLAM gives `(x, y, θ)` by matching the live scan to the map. This is your primary "where am I."
2. **Visual place recognition = the camera's job.** During mapping, periodically grab a camera frame, compute **ORB features (OpenCV)**, and save that "visual fingerprint" tagged with the LiDAR `(x, y)`. This builds a **keyframe database**.
3. **Relocalization ("GPS fix").** When the robot is unsure or gets **picked up and moved** (the "kidnapped robot" problem — common for vacuums), it matches its current camera view against the keyframe DB to recover a **coarse global position**, then LiDAR refines it.

This gives the camera-based-location feel described, while staying realistic on a ROCK 4C+. (Full monocular visual SLAM like ORB-SLAM3 is too heavy / too advanced here — we deliberately avoid it.)

### Obstacle avoidance = LiDAR-first, camera + sensors backup

The **LiDAR is also the primary obstacle sensor**, not just the mapper. The same scan that builds the map detects anything in its plane (walls, furniture legs, a chair that moved), so the navigation layer avoids obstacles directly from live LiDAR. The other sensors fill the LiDAR's blind spots:

- **LiDAR (in-plane geometry)** → main obstacle detection + avoidance. *Primary.*
- **Camera (below/above the scan plane)** → low objects the LiDAR misses: cables, socks, pet messes. *Supplement.*
- **Bumper microswitches + IR cliff sensors** → physical last-resort: contact stop + stair/drop protection. *Safety net.*

The navigation layer fuses all three into one "is it safe to move here" check.

---

## Repo structure (custom Python) — scaffolded

```
robovac/
├── robot/                  # runs on the ROCK 4C+
│   ├── drivers/            # lidar_driver.py, camera.py, serial_link.py (to ESP32)
│   ├── perception/         # slam.py (BreezySLAM), odometry.py, visual_loc.py (ORB DB)
│   ├── navigation/         # planner.py (A*/coverage), controller.py (drive to waypoint)
│   ├── comms/              # server_client.py (HTTP upload + MQTT telemetry)
│   └── main.py             # orchestrator loop / state machine
├── firmware/
│   └── esp32_motor/        # Arduino/PlatformIO: PWM, encoder counting, IMU read, serial proto
├── server/
│   ├── app.py              # FastAPI: map upload, REST, WebSocket live view
│   ├── planner.py          # room/coverage planning
│   ├── store/              # SQLite + saved map images
│   └── web/                # dashboard (HTML + canvas + JS)
├── shared/                 # message schemas shared by robot+server (pydantic)
├── tools/                  # log replay, map viewer, calibration scripts
├── tests/                  # schema + path-planning tests
└── docs/PLAN.md            # this document
```

**Libraries we reuse (don't reinvent):**
- `rplidar` (Python) — LiDAR scans. *(Backbone of perception.)*
- **BreezySLAM** (`simondlevy/BreezySLAM`) — drop-in 2D SLAM → occupancy grid + pose. *(Avoids writing SLAM math from scratch.)*
- **OpenCV** — ORB features for the visual keyframe DB; camera capture.
- **FastAPI + Uvicorn** — server API + WebSocket.
- **paho-mqtt** + **Mosquitto** — realtime pose/status telemetry.
- **NumPy** — grid math, A* path planning.
- **pydantic** — shared message schemas (`shared/`).

> Honest note: custom Python was chosen over ROS 2. That's fine and simpler to start, but if you later hit walls on robust navigation/localization, **ROS 2 (Nav2 + slam_toolbox)** gives those for free. The structure above keeps modules swappable so a future ROS migration wouldn't be a full rewrite.

---

## Milestone roadmap (each step is independently testable)

- ✅ **Step 0 — Repo bootstrap.** Git repository initialized and pushed to GitHub.
- ✅ **M0 (partial) — Repo scaffold.** Package skeleton created (`robot/ firmware/ server/ shared/ tools/ tests/`); navigation + schema logic implemented and unit-tested (8 passing). *Still to do:* flash newest Radxa Debian to the ROCK and set up venvs on the robot + server hosts.

**M1 — LiDAR alive.** Wire RPLidar over USB; run `python -m robot.drivers.lidar_driver` to print a live scan. *Test: a matplotlib polar plot of your room outline.*

**M2 — Drive base + odometry.** ESP32 firmware: drive 2 motors, count encoders, read IMU; serial protocol (`V left right` out; `O encL encR yaw` in — see `firmware/esp32_motor/README.md`). Python `odometry.py` integrates pose. *Test: drive a known 1 m square, compare reported vs measured pose.*

**M3 — Onboard SLAM.** Feed LiDAR (+odometry) into BreezySLAM; render the live occupancy grid + robot pose. *Test: push the robot around a room by hand and watch a recognizable map build.*

**M4 — Autonomous motion + LiDAR obstacle avoidance.** `controller.py` drives to a waypoint using SLAM pose; reject/replan paths that hit live-LiDAR obstacles; add bump/cliff safety stop. *Test: click a point on the map, robot drives there and steers around an object you place in its way, stopping on contact/cliff.*

**M5 — Server + map upload + dashboard.** FastAPI map store; robot uploads finished map; web dashboard renders map + live robot dot via MQTT/WebSocket. *Test: open the dashboard in a browser, see the house map and the robot moving in real time.*

**M6 — Coverage path planning.** `planner.py` generates a boustrophedon (back-and-forth) coverage path over free cells; robot executes it; mark cleaned cells. *Test: robot covers a whole room; dashboard shows coverage %.*

**M7 — Visual GPS layer.** Build the ORB keyframe DB during mapping; add relocalization on startup / after pickup. *Test: pick the robot up, move it to another room, it re-finds its position on the map.*

**M8 (polish) — Multi-room, no-go zones, scheduling, dock/return.** Server-side room labels + no-go zones; "clean kitchen" command; return-to-dock.

---

## Server design (details)

- **Map upload:** `POST /maps` with occupancy grid (PNG + metadata: resolution, origin). Stored in SQLite + a files dir.
- **Live telemetry:** robot publishes pose/status to MQTT topic `robovac/<id>/status`; dashboard subscribes via server WebSocket bridge.
- **Commands:** `POST /commands` (start/stop, clean-room, go-to) → robot polls or subscribes via MQTT.
- **Dashboard:** single HTML page, `<canvas>` draws the grid + a moving dot + planned path; buttons for start/stop/room select.
- **Planner:** runs on the server (not latency-critical); returns a waypoint list the robot executes locally.

---

## Risks & gotchas (call out early)

- **Old ROCK OS images** → use newest Radxa Debian + venv/Docker, or some libs won't build.
- **BreezySLAM build issues on ARM/new Python** are reported by some users — validate at M3; fallback is a simple scan-match + occupancy grid we write, or reconsider ROS `slam_toolbox`.
- **Odometry drift** is the #1 beginner SLAM problem → the IMU (BNO055) and good encoder counts matter; calibrate at M2.
- **LiDAR mounting:** must have a clear 360° view, above the chassis lip.
- **Power:** give the SBC a clean, separate 5V rail from the motors, or brownouts/resets will plague you.
- **Scope:** this is a big build — M1–M3 is a satisfying "it maps!" milestone; don't try to do everything at once.

---

## Overall verification strategy

- **Per-milestone tests** are listed above — each produces a visible result (a plot, a map, a moving dot, a cleaned room).
- **Log + replay:** record LiDAR/odometry logs (`tools/record_logs.py` → `tools/replay.py`) so SLAM/nav can be tested off-robot on the dev PC without driving the hardware every time.
- **Server tested independently:** feed it a saved map + fake MQTT pose stream to validate the dashboard before the robot is ready.
- **End-to-end (definition of done for v1):** robot maps a room → uploads to server → dashboard shows it → you click "clean" → robot runs a coverage path and reports progress → you pick it up, move it, and it re-localizes.

---

## Confirmed decisions

- **Brain:** Radxa ROCK 4C+ 4GB (newest Radxa Debian + Python venv/Docker).
- **Stack:** custom Python (ROS 2 kept as a future escape hatch).
- **SLAM:** onboard; server stores the map + plans cleaning paths.
- **Camera role:** LiDAR is the backbone for mapping **and** obstacle avoidance; camera = "visual GPS" place-recognition/relocalization **plus** catching low obstacles the LiDAR misses; bumper/cliff sensors are the safety net.
