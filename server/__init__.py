"""Server: map storage, dashboard, and high-level cleaning path planning.

Runs on an always-on box (a PC or small home server). It is NOT in the
robot's real-time loop — the robot navigates locally and uses the server for
storage, the dashboard, and non-urgent planning.
"""
