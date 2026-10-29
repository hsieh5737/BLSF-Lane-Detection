#pragma once
#include <opencv2/opencv.hpp>
namespace blsf {
cv::Mat weighted_gray(const cv::Mat& bgr, double w_r, double w_g, double w_b);
} // namespace blsf
