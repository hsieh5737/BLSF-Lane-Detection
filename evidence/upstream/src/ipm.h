#pragma once
#include <opencv2/opencv.hpp>
#include <string>

namespace blsf {

struct IPM {
  int bev_w = 640;
  int bev_h = 480;
  cv::Mat H; // 3x3
  bool ready = false;
};

bool pick_homography_ui(const cv::Mat& frame, IPM& ipm);
cv::Mat warp_to_bev(const cv::Mat& frame, const IPM& ipm);

bool save_homography(const std::string& path, const IPM& ipm);
bool load_homography(const std::string& path, IPM& ipm);

} // namespace blsf
