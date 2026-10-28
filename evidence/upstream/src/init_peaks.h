#pragma once
#include <opencv2/opencv.hpp>

namespace blsf {
struct Peaks {
  int x_left=-1;
  int x_right=-1;
  int lane_width=-1;
  cv::Mat histogram; // 1xW CV_32S
};
Peaks find_initial_peaks(const cv::Mat& feat, int smooth_ksize, int min_peak_value);
} // namespace blsf
