#include "blsf.h"
#include <algorithm>

namespace blsf {

static inline bool in_range(float x, float lo, float hi){ return (x>=lo && x<=hi); }

void blsf_filter(const std::vector<Segment>& in, std::vector<Segment>& out, const BLSFConfig& cfg, VoteInfo& info) {
  out.clear();
  info = VoteInfo{};

  std::vector<Segment> cand;
  cand.reserve(in.size());
  for (auto& s : in) {
    float a = std::abs(s.theta_deg);
    if (a < cfg.min_abs_angle || a > cfg.max_abs_angle) continue;
    cand.push_back(s);
  }

  for (auto& s : cand) {
    float th = s.theta_deg;
    if (in_range(th, cfg.a0_lo, cfg.a0_hi)) info.B0 += s.len;
    if (in_range(th, cfg.a1_lo, cfg.a1_hi)) info.B1 += s.len;
    if (in_range(th, cfg.a2_lo, cfg.a2_hi)) info.B2 += s.len;
  }

  float total = info.B0 + info.B1 + info.B2;
  float Bmax = info.B0; info.dom=0;
  if (info.B1 > Bmax) { Bmax=info.B1; info.dom=1; }
  if (info.B2 > Bmax) { Bmax=info.B2; info.dom=2; }
  info.dom_ratio = (total>1e-6f) ? (Bmax/total) : 0.f;

  if (total < cfg.min_total_vote || info.dom_ratio < cfg.min_dom_ratio) {
    info.low_confidence = true;
    return;
  }

  float base_lo=0, base_hi=0;
  if (info.dom==0) { base_lo=cfg.a0_lo; base_hi=cfg.a0_hi; }
  else if (info.dom==1) { base_lo=cfg.a1_lo; base_hi=cfg.a1_hi; }
  else { base_lo=cfg.a2_lo; base_hi=cfg.a2_hi; }

  info.TL = base_lo - cfg.delta_theta;
  info.TU = base_hi + cfg.delta_theta;

  for (auto& s : cand) {
    if (in_range(s.theta_deg, info.TL, info.TU)) out.push_back(s);
  }
}

cv::Mat segments_mask(const std::vector<Segment>& segs, int w, int h, int thickness) {
  cv::Mat mask(h, w, CV_8U, cv::Scalar(0));
  for (auto& s : segs) {
    cv::line(mask,
      cv::Point((int)std::round(s.x1),(int)std::round(s.y1)),
      cv::Point((int)std::round(s.x2),(int)std::round(s.y2)),
      cv::Scalar(255), thickness, cv::LINE_AA);
  }
  return mask;
}

} // namespace blsf
