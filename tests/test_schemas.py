"""Schemas round-trip through JSON (the wire format robot<->server use)."""

from shared.schemas import (
    Command,
    CommandType,
    Pose2D,
    RobotState,
    RobotStatus,
)


def test_pose_roundtrip():
    p = Pose2D(x=1.0, y=-2.5, theta=0.3)
    assert Pose2D.model_validate_json(p.model_dump_json()) == p


def test_status_roundtrip():
    s = RobotStatus(
        robot_id="robovac-01",
        state=RobotState.MAPPING,
        pose=Pose2D(x=0, y=0, theta=0),
        coverage_pct=42.0,
    )
    back = RobotStatus.model_validate_json(s.model_dump_json())
    assert back.state is RobotState.MAPPING
    assert back.coverage_pct == 42.0


def test_command_defaults():
    c = Command(type=CommandType.STOP)
    assert c.room is None and c.target is None
