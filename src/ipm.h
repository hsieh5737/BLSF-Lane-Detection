#pragma once
#include <opencv2/opencv.hpp>
#include <string>

namespace blsf {

struct IPM {
  int bev_w = 640;
  int bev_h = 480;
  // Declared ground ROI aspect (lateral width / forward length); 0 = undeclared.
  // Only used to report what the pixel-angle bands mean physically.
  double roi_w_over_l = 0;
  cv::Mat H; // 3x3
  bool ready = false;
};

bool pick_homography_ui(const cv::Mat& frame, IPM& ipm);
cv::Mat warp_to_bev(const cv::Mat& frame, const IPM& ipm);

bool save_homography(const std::string& path, const IPM& ipm);
bool load_homography(const std::string& path, IPM& ipm);
// Loads a homography only if its stored BEV size equals ipm.bev_w x ipm.bev_h
// (the configured size). Pixel-unit thresholds and angle bands are defined for
// one BEV grid, so a size mismatch is rejected instead of silently adopted.
bool load_homography_matching(const std::string& path, IPM& ipm);

} // namespace blsf
