#include "visualize.h"

namespace blsf {

cv::Mat draw_segments(const cv::Mat& img, const std::vector<Segment>& segs, const cv::Scalar& color, int thickness) {
  cv::Mat out = img.clone();
  for (auto& s : segs) {
    cv::line(out, cv::Point((int)s.x1,(int)s.y1), cv::Point((int)s.x2,(int)s.y2), color, thickness, cv::LINE_AA);
  }
  return out;
}

cv::Mat draw_windows(const cv::Mat& img, const TrackResult& tr) {
  cv::Mat out = img.clone();
  for (auto& r : tr.windows_left)  cv::rectangle(out, r, cv::Scalar(0,255,0), 2);
  for (auto& r : tr.windows_right) cv::rectangle(out, r, cv::Scalar(255,0,0), 2);
  return out;
}

cv::Mat draw_polys(const cv::Mat& img, const Poly2& left, const Poly2& right) {
  cv::Mat out = img.clone();
  auto draw_one = [&](const Poly2& p, const cv::Scalar& c) {
    if (!p.valid) return;
    std::vector<cv::Point> pts;
    for (int y=0; y<out.rows; y+=5) {
      double x = eval_poly_x(p, (double)y);
      if (x>=0 && x<out.cols) pts.emplace_back((int)std::round(x), y);
    }
    for (size_t i=1;i<pts.size();++i) cv::line(out, pts[i-1], pts[i], c, 3, cv::LINE_AA);
  };
  draw_one(left,  cv::Scalar(0,255,0));
  draw_one(right, cv::Scalar(0,0,255));
  return out;
}

} // namespace blsf
