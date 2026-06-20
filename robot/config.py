"""Central runtime configuration for the robot.

Values can be overridden with environment variables so you don't hardcode
ports / URLs. Edit defaults here for your hardware.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass(frozen=True)
class Config:
    # --- Identity ---
    robot_id: str = _env("ROBOVAC_ID", "robovac-01")

    # --- Hardware ports ---
    lidar_port: str = _env("ROBOVAC_LIDAR_PORT", "/dev/ttyUSB0")
    mcu_port: str = _env("ROBOVAC_MCU_PORT", "/dev/ttyACM0")  # ESP32 serial
    mcu_baud: int = int(_env("ROBOVAC_MCU_BAUD", "115200"))
    camera_index: int = int(_env("ROBOVAC_CAMERA", "0"))

    # --- Map / SLAM ---
    map_size_pixels: int = int(_env("ROBOVAC_MAP_PIXELS", "800"))
    map_size_meters: float = float(_env("ROBOVAC_MAP_METERS", "16"))

    # --- Server ---
    server_url: str = _env("ROBOVAC_SERVER_URL", "http://localhost:8000")
    mqtt_host: str = _env("ROBOVAC_MQTT_HOST", "localhost")
    mqtt_port: int = int(_env("ROBOVAC_MQTT_PORT", "1883"))

    @property
    def map_resolution(self) -> float:
        """Meters per cell."""
        return self.map_size_meters / self.map_size_pixels


CONFIG = Config()
