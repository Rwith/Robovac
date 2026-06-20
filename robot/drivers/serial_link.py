"""Serial link to the ESP32 motor controller.

Protocol (newline-delimited ASCII, see firmware/esp32_motor/README.md):

    PC -> ESP32:   "V <left_mps> <right_mps>\n"   set wheel speeds (m/s)
                   "S\n"                            emergency stop
    ESP32 -> PC:   "O <encL> <encR> <yaw_rad>\n"    odometry feedback
                   "B <bump_l> <bump_r> <cliff>\n"  safety sensors (0/1)

Keep this dumb: it just reads/writes lines. Odometry math lives in
perception/odometry.py.
"""

from __future__ import annotations

import serial  # pyserial

from robot.config import CONFIG


class SerialLink:
    def __init__(self, port: str | None = None, baud: int | None = None) -> None:
        self._ser = serial.Serial(
            port or CONFIG.mcu_port,
            baud or CONFIG.mcu_baud,
            timeout=0.05,
        )

    def set_wheel_speeds(self, left_mps: float, right_mps: float) -> None:
        self._ser.write(f"V {left_mps:.3f} {right_mps:.3f}\n".encode())

    def stop(self) -> None:
        self._ser.write(b"S\n")

    def read_line(self) -> str | None:
        line = self._ser.readline().decode(errors="ignore").strip()
        return line or None

    def close(self) -> None:
        self._ser.close()
