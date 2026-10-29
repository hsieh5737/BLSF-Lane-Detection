#include "ipm.h"
#include <vector>

namespace blsf {

struct ClickState {
  std::vector<cv::Point2f> pts;
  cv::Mat shown;
};

static void on_mouse(int event, int x, int y, int, void* userdata) {
  auto* st = reinterpret_cast<ClickState*>(userdata);
  if (event == cv::EVENT_LBUTTONDOWN) {
    if (st->pts.size() < 4) st->pts.emplace_back((float)x, (float)y);
  }
}

bool pick_homography_ui(const cv::Mat& frame, IPM& ipm) {
  ClickState st;
  const std::string win = "Pick 4 points: TL->TR->BR->BL (Enter=OK, r=reset, Esc=cancel)";
  cv::namedWindow(win, cv::WINDOW_NORMAL);
  cv::setMouseCallback(win, on_mouse, &st);

  for (;;) {
    st.shown = frame.clone();
    for (size_t i=0;i<st.pts.size();++i) {
      cv::circle(st.shown, st.pts[i], 5, cv::Scalar(0,255,0), -1);
      cv::putText(st.shown, std::to_string((int)i+1), st.pts[i]+cv::Point2f(6,-6),
                  cv::FONT_HERSHEY_SIMPLEX, 0.7, cv::Scalar(0,255,0), 2);
    }
    cv::imshow(win, st.shown);
    int k = cv::waitKey(20);
    if (k == 27) { cv::destroyWindow(win); return false; }     // Esc
    if (k == 'r' || k == 'R') { st.pts.clear(); continue; }    // reset
    if ((k == 13 || k == 10) && st.pts.size()==4) break;       // Enter
  }
  cv::destroyWindow(win);

  std::vector<cv::Point2f> src = st.pts;
  std::vector<cv::Point2f> dst = {
    {0.f, 0.f},
    {(float)(ipm.bev_w-1), 0.f},
    {(float)(ipm.bev_w-1), (float)(ipm.bev_h-1)},
    {0.f, (float)(ipm.bev_h-1)}
  };
  ipm.H = cv::getPerspectiveTransform(src, dst);
  ipm.ready = !ipm.H.empty();
  return ipm.ready;
}

cv::Mat warp_to_bev(const cv::Mat& frame, const IPM& ipm) {
  cv::Mat bev;
  cv::warpPerspective(frame, bev, ipm.H, cv::Size(ipm.bev_w, ipm.bev_h), cv::INTER_LINEAR);
  return bev;
}

bool save_homography(const std::string& path, const IPM& ipm) {
  cv::FileStorage fs(path, cv::FileStorage::WRITE);
  if (!fs.isOpened()) return false;
  fs << "bev_w" << ipm.bev_w;
  fs << "bev_h" << ipm.bev_h;
  fs << "H" << ipm.H;
  fs.release();
  return true;
}

bool load_homography(const std::string& path, IPM& ipm) {
  cv::FileStorage fs(path, cv::FileStorage::READ);
  if (!fs.isOpened()) return false;
  fs["bev_w"] >> ipm.bev_w;
  fs["bev_h"] >> ipm.bev_h;
  fs["H"] >> ipm.H;
  fs.release();
  ipm.ready = !ipm.H.empty();
  return ipm.ready;
}

bool load_homography_matching(const std::string& path, IPM& ipm) {
  IPM loaded;
  try {
    if (!load_homography(path, loaded)) return false;
  } catch (const cv::Exception&) {
    return false;
  }
  if (loaded.bev_w != ipm.bev_w || loaded.bev_h != ipm.bev_h) return false;
  if (loaded.H.rows != 3 || loaded.H.cols != 3) return false;
  loaded.roi_w_over_l = ipm.roi_w_over_l; // declared by the configuration
  ipm = loaded;
  return true;
}

} // namespace blsf
