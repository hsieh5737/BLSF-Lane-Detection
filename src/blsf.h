#pragma once
#include <string>
#include <vector>
#include <opencv2/opencv.hpp>
#include "lsd.h"

namespace blsf {

// Published Eq. (4) bands and the fixed overall envelope of this correction.
constexpr float kMaxAbsAngleDeg = 35.f;

struct BLSFConfig {
  float a0_lo=-35, a0_hi=0;
  float a1_lo=-5,  a1_hi=5;
  float a2_lo=0,   a2_hi=35;
  float delta_theta=0;     // must stay 0: selected published band, no expansion
  float min_total_vote=300; // absolute evidence threshold on max_k B_k (px of segment length)
  float min_abs_angle=0;   // must stay 0: no near-vertical exclusion
  float max_abs_angle=35;  // must stay 35: fixed overall envelope
  float min_len=20;        // strict >; synchronized with LSD by pipeline
  int draw_thickness=2;
  std::string gate="selected"; // confidence gate on the selected band's B ("selected") or on max_k B_k ("max", paper Sec. 2.2); identical for decision=sum
  std::string decision="sum"; // "sum": Eq. (6) argmax B_k (v1); "density": argmax B_k / band width
};

struct VoteInfo {
  float B0=0,B1=0,B2=0;
  int dom=-1;
  float dom_ratio=0;       // diagnostic only: max_k B_k / unique length, always >= 0.5
  bool low_confidence=false;
  float TL=0,TU=0;
  float unique_vote=0;     // sum of unique eligible segment lengths
  float retained_vote=0;   // max_k B_k = total length of segments passed to the tracker
};

void blsf_filter(const std::vector<Segment>& in, std::vector<Segment>& out, const BLSFConfig& cfg, VoteInfo& info);
bool valid_blsf_config(const BLSFConfig& cfg);
cv::Mat segments_mask(const std::vector<Segment>& segs, int w, int h, int thickness);
cv::Mat select_features(const cv::Mat& binary, const cv::Mat& mask, const std::string& source);

} // namespace blsf
