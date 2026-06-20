"""Robot-side software that runs on the Radxa ROCK 4C+.

Subpackages:
    drivers/     hardware I/O (LiDAR, camera, serial link to the ESP32)
    perception/  SLAM, odometry, visual localization
    navigation/  path planning + motion control
    comms/       talking to the server (HTTP map upload, MQTT telemetry)
"""
