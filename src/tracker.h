#pragma once
#include <opencv2/opencv.hpp>
#include <vector>
#include "init_peaks.h"

namespace blsf {
struct TrackResult {
  std::vector<cv::Point> pts_left;
  std::vector<cv::Point> pts_right;
  std::vector<cv::Rect> windows_left;
  std::vector<cv::Rect> windows_right;
  int hits_left=0, hits_right=0;  // windows with >= minpix feature pixels
};
TrackResult sliding_window_track(const cv::Mat& feat, const Peaks& peaks, int n_windows, int margin, int minpix);
} // namespace blsf
