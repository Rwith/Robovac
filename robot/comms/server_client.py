"""Client the robot uses to talk to the server.

  * upload_map()    POST the finished occupancy grid (HTTP, not latency-critical)
  * publish_status() push realtime pose/state over MQTT
  * commands are received by subscribing to an MQTT topic

The robot keeps navigating even if the server is unreachable — comms are
best-effort on purpose.
"""

from __future__ import annotations

import json
from collections.abc import Callable

import requests

from robot.config import CONFIG
from shared.schemas import Command, MapUpload, RobotStatus

try:
    import paho.mqtt.client as mqtt  # type: ignore
except ImportError:
    mqtt = None  # type: ignore


class ServerClient:
    def __init__(self) -> None:
        self._mqtt = None
        if mqtt is not None:
            self._mqtt = mqtt.Client(client_id=CONFIG.robot_id)
            self._mqtt.connect(CONFIG.mqtt_host, CONFIG.mqtt_port)
            self._mqtt.loop_start()

    # --- HTTP ---
    def upload_map(self, meta: MapUpload, image_png: bytes) -> bool:
        try:
            r = requests.post(
                f"{CONFIG.server_url}/maps",
                data={"meta": meta.model_dump_json()},
                files={"image": ("map.png", image_png, "image/png")},
                timeout=10,
            )
            return r.ok
        except requests.RequestException:
            return False

    # --- MQTT ---
    def publish_status(self, status: RobotStatus) -> None:
        if self._mqtt:
            self._mqtt.publish(
                f"robovac/{CONFIG.robot_id}/status", status.model_dump_json()
            )

    def on_command(self, handler: Callable[[Command], None]) -> None:
        if not self._mqtt:
            return
        topic = f"robovac/{CONFIG.robot_id}/command"

        def _cb(_c, _u, msg):  # noqa: ANN001
            handler(Command(**json.loads(msg.payload)))

        self._mqtt.subscribe(topic)
        self._mqtt.message_callback_add(topic, _cb)
