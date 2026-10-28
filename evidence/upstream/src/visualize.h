#pragma once
#include <opencv2/opencv.hpp>
#include <vector>
#include "lsd.h"
#include "tracker.h"
#include "ransac_fit.h"

namespace blsf {
cv::Mat draw_segments(const cv::Mat& img, const std::vector<Segment>& segs, const cv::Scalar& color, int thickness);
cv::Mat draw_windows(const cv::Mat& img, const TrackResult& tr);
cv::Mat draw_polys(const cv::Mat& img, const Poly2& left, const Poly2& right);
} // namespace blsf
