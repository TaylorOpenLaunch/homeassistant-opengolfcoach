"""Minimal 3D vector helpers."""
from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass
class Vec3:
    """Simple 3D vector class used for trajectory calculations."""

    x: float
    y: float
    z: float

    def __add__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> "Vec3":
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> "Vec3":
        return self.__mul__(scalar)

    def dot(self, other: "Vec3") -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def magnitude(self) -> float:
        return math.sqrt(self.dot(self))

    def normalize(self) -> "Vec3":
        mag = self.magnitude()
        if mag == 0:
            return Vec3(0.0, 0.0, 0.0)
        return Vec3(self.x / mag, self.y / mag, self.z / mag)

    def clamp(self, min_value: float, max_value: float) -> "Vec3":
        return Vec3(
            max(min(self.x, max_value), min_value),
            max(min(self.y, max_value), min_value),
            max(min(self.z, max_value), min_value),
        )
