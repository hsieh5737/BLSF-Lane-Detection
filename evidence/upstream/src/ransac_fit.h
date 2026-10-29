#pragma once
#include <opencv2/opencv.hpp>
#include <vector>

namespace blsf {

struct Poly2 { double a=0,b=0,c=0; bool valid=false; }; // x=a*y^2+b*y+c

struct RansacResult {
  Poly2 poly;
  int inliers=0;
  double score=1e18;
  std::vector<char> inlier_mask;
};

double eval_poly_x(const Poly2& p, double y);
RansacResult fit_parabola_ransac(const std::vector<cv::Point>& pts, int iters, double inlier_thresh, int min_inliers);

} // namespace blsf
