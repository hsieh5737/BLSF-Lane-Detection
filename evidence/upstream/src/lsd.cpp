#include "lsd.h"
#include "utils.h"

namespace blsf {

void detect_segments_lsd(const cv::Mat& gray8, std::vector<Segment>& segs, float min_len) {
  CV_Assert(gray8.type()==CV_8U);
  segs.clear();

  cv::Ptr<cv::LineSegmentDetector> lsd = cv::createLineSegmentDetector(cv::LSD_REFINE_STD);
  std::vector<cv::Vec4f> lines;
  lsd->detect(gray8, lines);

  for (auto& v : lines) {
    float x1=v[0], y1=v[1], x2=v[2], y2=v[3];
    float dx=x2-x1, dy=y2-y1;
    float len=std::sqrt(dx*dx + dy*dy);
    if (len < min_len) continue;
    float theta = rad2deg(std::atan2(dy, dx));
    if (theta > 90.f) theta -= 180.f;
    if (theta < -90.f) theta += 180.f;
    segs.push_back({x1,y1,x2,y2,len,theta});
  }
}

} // namespace blsf
