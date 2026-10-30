#pragma once
#include <opencv2/opencv.hpp>
#include <string>

namespace blsf {
struct Peaks {
  int x_left=-1;
  int x_right=-1;
  int lane_width=-1;
  cv::Mat histogram; // 1xW CV_32S
};

// Defaults reproduce the registered (v1) behaviour: lower half of the BEV,
// global maximum in each half.
struct PeakOptions {
  double rows_fraction=0.5;        // histogram over the lowest rows_fraction of the BEV
  std::string select="max";        // "max" | "nearest_expected"
  int expected_offset=0;           // nearest_expected: expected |x - W/2| of the ego boundary (px)
  int max_offset=0;                // only peaks with |x - W/2| <= max_offset (0 = whole half)
  int min_offset=0;                // only peaks with |x - W/2| >= min_offset
  int min_width=0, max_width=0;    // nearest_expected: admissible x_right - x_left (0 = no pair check)
};

Peaks find_initial_peaks(const cv::Mat& feat, int smooth_ksize, int min_peak_value,
                         const PeakOptions& opt = PeakOptions());
} // namespace blsf
