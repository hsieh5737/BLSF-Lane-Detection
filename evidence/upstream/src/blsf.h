#pragma once
#include <vector>
#include <opencv2/opencv.hpp>
#include "lsd.h"

namespace blsf {

struct BLSFConfig {
  float a0_lo=-35, a0_hi=0;
  float a1_lo=-5,  a1_hi=5;
  float a2_lo=0,   a2_hi=35;
  float delta_theta=12;
  float min_total_vote=300;
  float min_dom_ratio=0.40;
  float min_abs_angle=5;
  float max_abs_angle=85;
  int draw_thickness=2;
};

struct VoteInfo {
  float B0=0,B1=0,B2=0;
  int dom=-1;
  float dom_ratio=0;
  bool low_confidence=false;
  float TL=0,TU=0;
};

void blsf_filter(const std::vector<Segment>& in, std::vector<Segment>& out, const BLSFConfig& cfg, VoteInfo& info);
cv::Mat segments_mask(const std::vector<Segment>& segs, int w, int h, int thickness);

} // namespace blsf
