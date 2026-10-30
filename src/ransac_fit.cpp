#include "ransac_fit.h"
#include <random>
#include <cmath>
#include <algorithm>

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

RansacResult fit_parabola_ransac(const std::vector<cv::Point>& pts, int iters, double inlier_thresh, int min_inliers,
                                 double max_abs_a, bool refit, int linear_span) {
  RansacResult best;
  if ((int)pts.size() < 20) return best;

  std::mt19937 rng(12345);
  std::uniform_int_distribution<int> uni(0, (int)pts.size()-1);

  for (int it=0; it<iters; ++it) {
    int i1=uni(rng), i2=uni(rng), i3=uni(rng);
    if (i1==i2||i1==i3||i2==i3) continue;

    Poly2 p;
    if (!fit_from_3(pts[i1], pts[i2], pts[i3], p)) continue;
    if (max_abs_a > 0 && std::abs(p.a) > max_abs_a) continue;

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
  if (refit && best.poly.valid && best.inliers >= 3) {
    int ymin=1<<30, ymax=-1;
    for (size_t i=0;i<pts.size();++i) if (best.inlier_mask[i]) { ymin=std::min(ymin,pts[i].y); ymax=std::max(ymax,pts[i].y); }
    bool linear = linear_span > 0 && (ymax - ymin) < linear_span;
    int nc = linear ? 2 : 3;
    cv::Mat A((int)best.inliers, nc, CV_64F), X((int)best.inliers, 1, CV_64F);
    int r=0;
    for (size_t i=0;i<pts.size();++i) if (best.inlier_mask[i]) {
      double y=pts[i].y; int c=0;
      if (!linear) A.at<double>(r,c++)=y*y;
      A.at<double>(r,c++)=y; A.at<double>(r,c)=1; X.at<double>(r,0)=pts[i].x; ++r;
    }
    cv::Mat sol;
    if (cv::solve(A, X, sol, cv::DECOMP_SVD)) {
      Poly2 q; q.valid=true;
      if (linear) { q.a=0; q.b=sol.at<double>(0,0); q.c=sol.at<double>(1,0); }
      else { q.a=sol.at<double>(0,0); q.b=sol.at<double>(1,0); q.c=sol.at<double>(2,0); }
      if (!(max_abs_a > 0 && std::abs(q.a) > max_abs_a)) best.poly = q;
    }
  }
  return best;
}

} // namespace blsf
