# ESP32 Motor Controller

Real-time motor control, encoder counting, and IMU reading live here — off the
ROCK 4C+ so timing is reliable. The ESP32 talks to the SBC over USB serial.

## Serial protocol (115200 baud, newline-delimited ASCII)

| Direction | Message | Meaning |
|-----------|---------|---------|
| PC → ESP32 | `V <left_mps> <right_mps>` | set wheel speeds (m/s) |
| PC → ESP32 | `S` | emergency stop |
| ESP32 → PC | `O <encL> <encR> <yaw_rad>` | odometry feedback (~50 Hz) |
| ESP32 → PC | `B <bump_l> <bump_r> <cliff>` | safety sensors (0/1) |

Matches `robot/drivers/serial_link.py`.

## Hardware

- ESP32 devkit
- TB6612FNG dual motor driver (drive wheels)
- 2× quadrature encoders (interrupt pins)
- BNO055 IMU (I²C) for yaw
- Bumper microswitches + IR cliff sensors

## Build

PlatformIO: `pio run -t upload` from this folder.
