#pragma once
#include <cmath>
#include <limits>
namespace blsf {
// Undirected angle from upward BEV vertical: x right, y down.
// Positive = rightward as y decreases. Swapping endpoints is invariant.
inline float vertical_angle_deg(float dx, float dy) {
  if (!std::isfinite(dx) || !std::isfinite(dy) || (dx == 0 && dy == 0))
    return std::numeric_limits<float>::quiet_NaN();
  double a = std::atan2(double(dx), -double(dy)) * 180.0 / std::acos(-1.0);
  a = std::fmod(a + 90.0, 180.0);
  if (a < 0) a += 180.0;
  return static_cast<float>(a - 90.0); // [-90,90)
}
} // namespace blsf
