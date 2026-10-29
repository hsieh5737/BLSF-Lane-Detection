#include "pipeline.h"
#include "preprocess.h"
#include "mlt.h"
#include "lsd.h"
#include "visualize.h"

namespace blsf {

bool load_config_yaml(const std::string& path, Config& cfg) {
  cv::FileStorage fs(path, cv::FileStorage::READ);
  if (!fs.isOpened()) return false;

  fs["ipm"]["bev_width"] >> cfg.ipm.bev_w;
  fs["ipm"]["bev_height"] >> cfg.ipm.bev_h;

  fs["gray"]["w_r"] >> cfg.w_r;
  fs["gray"]["w_g"] >> cfg.w_g;
  fs["gray"]["w_b"] >> cfg.w_b;

  fs["mlt"]["median_ksize"] >> cfg.mlt_k;
  fs["mlt"]["offset_t"] >> cfg.mlt_t;

  fs["lsd"]["min_len"] >> cfg.lsd_min_len;
  fs["lsd"]["min_abs_angle"] >> cfg.blsf.min_abs_angle;
  fs["lsd"]["max_abs_angle"] >> cfg.blsf.max_abs_angle;

  fs["blsf"]["a0_lo"] >> cfg.blsf.a0_lo;
  fs["blsf"]["a0_hi"] >> cfg.blsf.a0_hi;
  fs["blsf"]["a1_lo"] >> cfg.blsf.a1_lo;
  fs["blsf"]["a1_hi"] >> cfg.blsf.a1_hi;
  fs["blsf"]["a2_lo"] >> cfg.blsf.a2_lo;
  fs["blsf"]["a2_hi"] >> cfg.blsf.a2_hi;
  fs["blsf"]["delta_theta"] >> cfg.blsf.delta_theta;
  fs["blsf"]["min_total_vote"] >> cfg.blsf.min_total_vote;
  fs["blsf"]["min_dom_ratio"] >> cfg.blsf.min_dom_ratio;
  fs["blsf"]["draw_thickness"] >> cfg.blsf.draw_thickness;

  fs["features"]["source"] >> cfg.feat_source;
  fs["features"]["hybrid_or"] >> cfg.hybrid_or;

  fs["peaks"]["smooth_ksize"] >> cfg.peaks_smooth;
  fs["peaks"]["min_peak_value"] >> cfg.peaks_min;

  fs["tracker"]["n_windows"] >> cfg.n_windows;
  fs["tracker"]["margin"] >> cfg.margin;
  fs["tracker"]["minpix"] >> cfg.minpix;

  fs["ransac"]["iters"] >> cfg.ransac_iters;
  fs["ransac"]["inlier_thresh"] >> cfg.ransac_thresh;
  fs["ransac"]["min_inliers"] >> cfg.ransac_min_inliers;

  fs.release();
  return true;
}

RunResult run_pipeline(const cv::Mat& bgr, Config& cfg, DebugPack& dbg) {
  RunResult rr;

  // 1) IPM
  dbg.bev_bgr = warp_to_bev(bgr, cfg.ipm);

  // 2) weighted gray
  dbg.gray = weighted_gray(dbg.bev_bgr, cfg.w_r, cfg.w_g, cfg.w_b);

  // 3) MLT
  mlt_binarize(dbg.gray, dbg.binary, dbg.median, cfg.mlt_k, cfg.mlt_t);

  // 4) LSD on binary
  std::vector<Segment> segs;
  detect_segments_lsd(dbg.binary, segs, cfg.lsd_min_len);
  cv::Mat bin_bgr; cv::cvtColor(dbg.binary, bin_bgr, cv::COLOR_GRAY2BGR);
  dbg.seg_before = draw_segments(bin_bgr, segs, cv::Scalar(0,255,255), 2);

  // 5) BLSF
  std::vector<Segment> segf;
  blsf_filter(segs, segf, cfg.blsf, rr.vote);
  dbg.seg_after = draw_segments(bin_bgr, segf, cv::Scalar(0,255,0), 2);

  if (rr.vote.low_confidence) {
    rr.status = "low_confidence";
    dbg.seg_mask = cv::Mat::zeros(dbg.binary.size(), CV_8U);
    dbg.feat_used = dbg.binary.clone();
    cv::cvtColor(dbg.binary, dbg.windows_img, cv::COLOR_GRAY2BGR);
    dbg.overlay = dbg.bev_bgr.clone();
    return rr;
  }

  // 6) seg_mask + feature selection
  dbg.seg_mask = segments_mask(segf, dbg.binary.cols, dbg.binary.rows, cfg.blsf.draw_thickness);

  if (cfg.feat_source == "segments_mask") dbg.feat_used = dbg.seg_mask.clone();
  else if (cfg.feat_source == "binary") dbg.feat_used = dbg.binary.clone();
  else {
    if (cfg.hybrid_or) cv::bitwise_or(dbg.binary, dbg.seg_mask, dbg.feat_used);
    else cv::addWeighted(dbg.binary, 0.5, dbg.seg_mask, 0.5, 0.0, dbg.feat_used);
  }

  // 7) peaks
  rr.peaks = find_initial_peaks(dbg.feat_used, cfg.peaks_smooth, cfg.peaks_min);
  if (rr.peaks.x_left < 0 || rr.peaks.x_right < 0) {
    rr.status = "no_peaks";
    dbg.overlay = dbg.bev_bgr.clone();
    return rr;
  }

  // 8) windows
  TrackResult tr = sliding_window_track(dbg.feat_used, rr.peaks, cfg.n_windows, cfg.margin, cfg.minpix);
  cv::Mat feat_bgr; cv::cvtColor(dbg.feat_used, feat_bgr, cv::COLOR_GRAY2BGR);
  dbg.windows_img = draw_windows(feat_bgr, tr);

  // 9) RANSAC
  auto left_fit  = fit_parabola_ransac(tr.pts_left,  cfg.ransac_iters, cfg.ransac_thresh, cfg.ransac_min_inliers);
  auto right_fit = fit_parabola_ransac(tr.pts_right, cfg.ransac_iters, cfg.ransac_thresh, cfg.ransac_min_inliers);
  rr.left = left_fit.poly;
  rr.right = right_fit.poly;

  rr.ok = rr.left.valid && rr.right.valid;
  rr.status = rr.ok ? "ok" : "fit_failed";

  dbg.overlay = draw_polys(dbg.bev_bgr, rr.left, rr.right);
  return rr;
}

} // namespace blsf
