"""Simplified ball flight simulation."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from .unit_conversions import deg_to_rad
from .vector import Vec3

GRAVITY_MPS2 = 9.80665
DRAG_COEFF = 0.0025
LIFT_COEFF = 0.0006


@dataclass
class TrajectoryPoint:
    """Single trajectory sample."""

    time_s: float
    position_m: Vec3
    velocity_mps: Vec3


Trajectory = list[TrajectoryPoint]


def _initial_velocity(ball_speed_mps: float, vla_deg: float, hla_deg: float) -> Vec3:
    vla_rad = deg_to_rad(vla_deg)
    hla_rad = deg_to_rad(hla_deg)

    horizontal_speed = ball_speed_mps * math.cos(vla_rad)
    vx = horizontal_speed * math.cos(hla_rad)
    vy = horizontal_speed * math.sin(hla_rad)
    vz = ball_speed_mps * math.sin(vla_rad)
    return Vec3(vx, vy, vz)


def simulate_trajectory(
    ball_speed_mps: float,
    vertical_launch_angle_deg: float,
    horizontal_launch_angle_deg: float,
    spin_rpm: float,
    spin_axis_deg: float,
    time_step_s: float = 0.02,
    max_time_s: float = 10.0,
) -> Trajectory:
    """Simulate a shot trajectory with a deterministic drag/lift model."""
    velocity = _initial_velocity(
        ball_speed_mps,
        vertical_launch_angle_deg,
        horizontal_launch_angle_deg,
    )
    position = Vec3(0.0, 0.0, 0.0)
    spin_rps = spin_rpm / 60.0 * 2.0 * math.pi
    spin_axis_rad = deg_to_rad(spin_axis_deg)

    points: Trajectory = []
    time_s = 0.0

    while time_s <= max_time_s:
        points.append(TrajectoryPoint(time_s, position, velocity))

        if time_s > 0.0 and position.z <= 0.0:
            break

        speed = velocity.magnitude()
        if speed <= 0.0:
            break

        drag_mag = DRAG_COEFF * speed * speed
        drag_vec = velocity.normalize() * (-drag_mag)

        lift_mag = LIFT_COEFF * spin_rps * speed
        lift_mag = max(min(lift_mag, 20.0), -20.0)
        lift_vec = Vec3(0.0, lift_mag * math.sin(spin_axis_rad), lift_mag * math.cos(spin_axis_rad))

        accel = Vec3(
            drag_vec.x + lift_vec.x,
            drag_vec.y + lift_vec.y,
            drag_vec.z + lift_vec.z - GRAVITY_MPS2,
        )

        velocity = Vec3(
            velocity.x + accel.x * time_step_s,
            velocity.y + accel.y * time_step_s,
            velocity.z + accel.z * time_step_s,
        )
        position = Vec3(
            position.x + velocity.x * time_step_s,
            position.y + velocity.y * time_step_s,
            max(position.z + velocity.z * time_step_s, -0.5),
        )

        time_s += time_step_s

    return points


def iter_positions(points: Iterable[TrajectoryPoint]) -> Iterable[Vec3]:
    """Yield positions from a trajectory."""
    for point in points:
        yield point.position_m
