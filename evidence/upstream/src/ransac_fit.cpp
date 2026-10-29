#include "ransac_fit.h"
#include <random>
#include <cmath>

namespace blsf {

double eval_poly_x(const Poly2& p, double y) { return p.a*y*y + p.b*y + p.c; }

static bool fit_from_3(const cv::Point& p1, const cv::Point& p2, const cv::Point& p3, Poly2& out) {
  double y1=p1.y, y2=p2.y, y3=p3.y;
  double x1=p1.x, x2=p2.x, x3=p3.x;

  cv::Mat A = (cv::Mat_<double>(3,3) << y1*y1, y1, 1,  y2*y2, y2, 1,  y3*y3, y3, 1);
  cv::Mat X = (cv::Mat_<double>(3,1) << x1, x2, x3);
  if (std::abs(cv::determinant(A)) < 1e-9) return false;
  cv::Mat sol;
  if (!cv::solve(A, X, sol, cv::DECOMP_LU)) return false;
  out.a = sol.at<double>(0,0);
  out.b = sol.at<double>(1,0);
  out.c = sol.at<double>(2,0);
  out.valid = true;
  return true;
}

RansacResult fit_parabola_ransac(const std::vector<cv::Point>& pts, int iters, double inlier_thresh, int min_inliers) {
  RansacResult best;
  if ((int)pts.size() < 20) return best;

  std::mt19937 rng(12345);
  std::uniform_int_distribution<int> uni(0, (int)pts.size()-1);

  for (int it=0; it<iters; ++it) {
    int i1=uni(rng), i2=uni(rng), i3=uni(rng);
    if (i1==i2||i1==i3||i2==i3) continue;

    Poly2 p;
    if (!fit_from_3(pts[i1], pts[i2], pts[i3], p)) continue;

    int inl=0; double sse=0;
    std::vector<char> mask(pts.size(), 0);
    for (size_t i=0;i<pts.size();++i) {
      double xhat = eval_poly_x(p, (double)pts[i].y);
      double d = std::abs((double)pts[i].x - xhat);
      if (d <= inlier_thresh) { mask[i]=1; inl++; sse += d*d; }
    }
    if (inl < min_inliers) continue;

    bool better = (inl > best.inliers) || (inl==best.inliers && sse < best.score);
    if (better) {
      best.poly = p;
      best.inliers = inl;
      best.score = sse;
      best.inlier_mask.swap(mask);
    }
  }
  return best;
}

} // namespace blsf
