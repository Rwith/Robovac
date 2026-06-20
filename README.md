# Robovac

A 3D-printed robot vacuum that maps the house with a 2D LiDAR + camera (onboard SLAM),
uploads the map to a server for storage + path planning, and localizes itself using LiDAR
with a camera-based "visual GPS" relocalization layer.

## Decisions (v1)

- **Brain:** Radxa ROCK 4C+ (RK3399-T, 4GB) running a modern Radxa Debian image + Python venv.
- **Stack:** Custom Python (ROS 2 kept as a future escape hatch).
- **SLAM:** Runs onboard the robot; the server stores the map and plans cleaning paths.
- **Sensing:** LiDAR leads mapping **and** obstacle avoidance; camera adds visual
  place-recognition ("GPS") + catches low obstacles the LiDAR misses; bumper/cliff
  sensors are the safety net.

## Planned structure

```
robot/      # runs on the ROCK 4C+ (drivers, perception/SLAM, navigation, comms)
firmware/   # ESP32 motor + encoder + IMU controller (serial link to the SBC)
server/     # FastAPI map store, dashboard, coverage/path planner
shared/     # message schemas shared by robot + server
tools/      # log replay, map viewer, calibration
tests/
```

See the design plan for the full architecture, bill of materials, and milestone roadmap.

## Quickstart (dev PC, no hardware needed)

```bash
python -m venv .venv && . .venv/Scripts/activate   # Windows
pip install pydantic numpy pytest
pytest                                             # run the logic tests
```

The hardware-dependent modules (LiDAR, camera, SLAM, serial) import lazily, so
the package imports and the planner/schema tests run on any machine. Install
`robot/requirements.txt` on the ROCK 4C+ and `server/requirements.txt` on the
server host when you're ready for the real thing.

## Status

🚧 Scaffolding in place — modules are coherent stubs wired to the architecture,
with the navigation/schema logic implemented and tested. Each milestone
(M1 LiDAR → M8 multi-room) fills in one more piece. See the design plan.
