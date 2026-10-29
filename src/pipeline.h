#pragma once
#include <opencv2/opencv.hpp>
#include <string>
#include "ipm.h"
#include "blsf.h"
#include "init_peaks.h"
#include "tracker.h"
#include "ransac_fit.h"

namespace blsf {

struct Config {
  IPM ipm;
  double w_r=0.5, w_g=0.4, w_b=0.1;
  int mlt_k=11, mlt_t=15;
  float lsd_min_len=20.f;
  BLSFConfig blsf;
  std::string feat_source="segments_mask";
  bool blsf_enabled=true;
  int peaks_smooth=9, peaks_min=50;
  int n_windows=12, margin=60, minpix=40;
  int ransac_iters=200;
  double ransac_thresh=10.0;
  int ransac_min_inliers=80;
};

struct DebugPack {
  cv::Mat bev_bgr, gray, median, binary;
  cv::Mat seg_before, seg_after, seg_mask, feat_used;
  cv::Mat windows_img, overlay;
};

bool load_config_yaml(const std::string& path, Config& cfg);

struct RunResult {
  Poly2 left, right;
  bool ok=false;
  std::string status="ok";
  VoteInfo vote;
  Peaks peaks;
};

RunResult run_pipeline(const cv::Mat& bgr, Config& cfg, DebugPack& dbg);

} // namespace blsf
