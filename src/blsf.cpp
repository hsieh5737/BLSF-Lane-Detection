#include "blsf.h"
#include <algorithm>
#include <cmath>

namespace blsf {
static bool in_range(float x, float lo, float hi) { return x >= lo && x <= hi; }

bool valid_blsf_config(const BLSFConfig& c) {
  // This correction supports only the published bands, the fixed +/-35 degree
  // envelope, no hidden expansion and no exclusion around vertical.
  return c.a0_lo == -35 && c.a0_hi == 0 && c.a1_lo == -5 && c.a1_hi == 5 &&
    c.a2_lo == 0 && c.a2_hi == 35 && c.delta_theta == 0 &&
    c.min_abs_angle == 0 && c.max_abs_angle == kMaxAbsAngleDeg &&
    std::isfinite(c.min_len) && c.min_len >= 0 &&
    std::isfinite(c.min_total_vote) && c.min_total_vote > 0 &&
    c.draw_thickness >= 1 && c.draw_thickness <= 32;
}

void blsf_filter(const std::vector<Segment>& in, std::vector<Segment>& out,
                 const BLSFConfig& cfg, VoteInfo& info) {
  out.clear();
  info = VoteInfo{};
  info.low_confidence = true;
  if (!valid_blsf_config(cfg)) return;
  std::vector<Segment> cand;
  for (const auto& s : in) {
    if (!std::isfinite(s.x1) || !std::isfinite(s.y1) ||
        !std::isfinite(s.x2) || !std::isfinite(s.y2) ||
        !std::isfinite(s.len) || !std::isfinite(s.theta_deg) ||
        s.len <= cfg.min_len || std::hypot(s.x2-s.x1,s.y2-s.y1) == 0 ||
        std::abs(s.theta_deg) > cfg.max_abs_angle) continue;
    const float a = s.theta_deg;
    const bool b0 = in_range(a,cfg.a0_lo,cfg.a0_hi);
    const bool b1 = in_range(a,cfg.a1_lo,cfg.a1_hi);
    const bool b2 = in_range(a,cfg.a2_lo,cfg.a2_hi);
    // A0 and A2 jointly cover [-35,35], so every admissible segment votes.
    cand.push_back(s);
    if (b0) info.B0 += s.len;
    if (b1) info.B1 += s.len;
    if (b2) info.B2 += s.len;
    info.unique_vote += s.len;
  }
  // Overlapping membership follows Eq. (5). Tie order: straight, left, right.
  info.dom = 1;
  float bmax = info.B1;
  if (info.B0 > bmax) { bmax = info.B0; info.dom = 0; }
  if (info.B2 > bmax) { bmax = info.B2; info.dom = 2; }
  info.retained_vote = bmax;
  info.dom_ratio = info.unique_vote > 0 ? bmax / info.unique_vote : 0;
  // Paper Sec. 2.2: low-confidence when all bin scores are below the absolute
  // threshold, i.e. max_k B_k < threshold. Because the selected band equals the
  // winning bin, this is also the total segment length handed to the tracker.
  // No dominance-ratio gate: with A0 U A2 = [-35,35], dom_ratio >= 0.5 always.
  if (bmax < cfg.min_total_vote) return;
  info.TL = info.dom == 0 ? cfg.a0_lo : (info.dom == 1 ? cfg.a1_lo : cfg.a2_lo);
  info.TU = info.dom == 0 ? cfg.a0_hi : (info.dom == 1 ? cfg.a1_hi : cfg.a2_hi);
  for (const auto& s : cand)
    if (in_range(s.theta_deg,info.TL,info.TU)) out.push_back(s);
  info.low_confidence = out.empty();
}

cv::Mat segments_mask(const std::vector<Segment>& segs, int w, int h, int thickness) {
  cv::Mat mask(h,w,CV_8U,cv::Scalar(0));
  for (const auto& s : segs)
    cv::line(mask,cv::Point(cvRound(s.x1),cvRound(s.y1)),
             cv::Point(cvRound(s.x2),cvRound(s.y2)),cv::Scalar(255),thickness,cv::LINE_8);
  return mask; // Strict 0/255; rasterized support need not be a subset of binary.
}

cv::Mat select_features(const cv::Mat& binary, const cv::Mat& mask, const std::string& source) {
  CV_Assert(binary.type() == CV_8U && mask.type() == CV_8U && binary.size() == mask.size());
  if (source == "segments_mask") return mask.clone();
  if (source == "binary") return binary.clone(); // diagnostic control only
  if (source == "binary_and_segments") {
    cv::Mat out;
    cv::bitwise_and(binary,mask,out);
    return out;
  }
  CV_Error(cv::Error::StsBadArg,"Unknown feature source; legacy hybrid is unsupported");
}
} // namespace blsf
