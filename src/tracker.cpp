#include "tracker.h"
#include <algorithm>

namespace blsf {

static inline void collect_points_in_window(const cv::Mat& feat, const cv::Rect& win, std::vector<cv::Point>& out) {
  for (int y=win.y; y<win.y+win.height; ++y) {
    const uchar* row = feat.ptr<uchar>(y);
    for (int x=win.x; x<win.x+win.width; ++x) {
      if (row[x] > 0) out.emplace_back(x,y);
    }
  }
}

TrackResult sliding_window_track(const cv::Mat& feat, const Peaks& peaks, int n_windows, int margin, int minpix) {
  CV_Assert(feat.type()==CV_8U);
  TrackResult tr;
  int W=feat.cols, H=feat.rows;

  int xL=peaks.x_left, xR=peaks.x_right;
  if (xL<0 && xR<0) return tr;  // a missing side is skipped (callers decide whether one side suffices)

  int win_h = H / std::max(1, n_windows);

  for (int i=0;i<n_windows;++i) {
    int y_low  = H - (i+1)*win_h;
    cv::Rect winL(std::max(0,xL-margin), y_low, std::min(W, xL+margin)-std::max(0,xL-margin), win_h);
    cv::Rect winR(std::max(0,xR-margin), y_low, std::min(W, xR+margin)-std::max(0,xR-margin), win_h);
    winL &= cv::Rect(0,0,W,H);
    winR &= cv::Rect(0,0,W,H);

    std::vector<cv::Point> ptsW;
    ptsW.reserve(1024);
    if (xL>=0) {
      collect_points_in_window(feat, winL, ptsW);
      if ((int)ptsW.size() >= minpix) {
        int sumx=0;
        for (auto& p: ptsW){ sumx+=p.x; tr.pts_left.push_back(p); }
        xL = sumx/(int)ptsW.size();
      }
      tr.windows_left.push_back(winL);
    }

    if (xR>=0) {
      ptsW.clear();
      collect_points_in_window(feat, winR, ptsW);
      if ((int)ptsW.size() >= minpix) {
        int sumx=0;
        for (auto& p: ptsW){ sumx+=p.x; tr.pts_right.push_back(p); }
        xR = sumx/(int)ptsW.size();
      }
      tr.windows_right.push_back(winR);
    }
  }

  return tr;
}

} // namespace blsf
