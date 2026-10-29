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
// sx/sy (px per metre lateral / px per metre forward) of a BEV grid of
// bev_w x bev_h pixels covering a ground ROI with width/length = roi_w_over_l.
inline double bev_anisotropy(int bev_w, int bev_h, double roi_w_over_l) {
  return (double(bev_w) / double(bev_h)) / roi_w_over_l;
}
// Physical heading equivalent of a BEV pixel angle:
// tan(theta_pixel) = (sx/sy) tan(theta_physical).
inline double physical_angle_deg(double pixel_deg, double sx_over_sy) {
  const double r = std::acos(-1.0) / 180.0;
  return std::atan(std::tan(pixel_deg * r) / sx_over_sy) / r;
}
} // namespace blsf
