#pragma once
#include <opencv2/opencv.hpp>
#include <vector>

namespace blsf {
struct Segment {
  float x1,y1,x2,y2;
  float len;
  float theta_deg; // [-90,90), upward vertical reference, endpoint invariant
};
void detect_segments_lsd(const cv::Mat& gray8, std::vector<Segment>& segs, float min_len);
} // namespace blsf
