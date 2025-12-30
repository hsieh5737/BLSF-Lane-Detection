#pragma once
#include <opencv2/opencv.hpp>
namespace blsf {
void mlt_binarize(const cv::Mat& gray, cv::Mat& binary, cv::Mat& median, int median_ksize, int offset_t);
} // namespace blsf
