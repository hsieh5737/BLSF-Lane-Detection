#include "blsf.h"
#include "lsd.h"
#include <iostream>
#include <cmath>

int main() {
  using namespace blsf;
  cv::Mat b(480,640,CV_8U,cv::Scalar(0));
  cv::rectangle(b,{180,20},{186,460},cv::Scalar(255),-1);
  cv::rectangle(b,{450,20},{456,460},cv::Scalar(255),-1);
  std::vector<Segment> seg,out;
  detect_segments_lsd(b,seg,20);
  VoteInfo v; BLSFConfig c;
  blsf_filter(seg,out,c,v);
  std::cout << "opencv," << CV_VERSION << "\ncase,input,retained,low_confidence\n"
    << "vertical_rectangles," << seg.size() << "," << out.size() << "," << v.low_confidence << "\n";
  if (seg.empty() || !out.empty() || !v.low_confidence) return 1;
  for (float a : {80.f,30.f}) {
    float dx=300*std::cos(a*CV_PI/180),dy=300*std::sin(a*CV_PI/180);
    seg={{0,0,dx,dy,300,a},{100,0,100+dx,dy,300,a}};
    blsf_filter(seg,out,c,v);
    std::cout << "horizontal_reference_" << a << ",2," << out.size() << "," << v.low_confidence << "\n";
    if (a==80 && (!out.empty() || !v.low_confidence)) return 2;
    if (a==30 && (out.size()!=2 || v.low_confidence)) return 3;
  }
  // Rotate to vertical zero ONLY, retaining the old confidence denominator.
  seg={{0,300,0,0,300,0},{100,300,100,0,300,0}};
  c.min_abs_angle=0;
  blsf_filter(seg,out,c,v);
  std::cout << "axis_and_min_angle_only,2," << out.size() << "," << v.low_confidence << "\n";
  return (!out.empty() || !v.low_confidence) ? 4 : 0;
}
