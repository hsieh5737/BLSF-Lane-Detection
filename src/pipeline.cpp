#include "pipeline.h"
#include <cmath>
#include "preprocess.h"
#include "mlt.h"
#include "lsd.h"
#include "visualize.h"

namespace blsf {

bool load_config_yaml(const std::string& path, Config& cfg) {
  try {
  cv::FileStorage fs(path, cv::FileStorage::READ);
  if (!fs.isOpened()) return false;

  fs["ipm"]["bev_width"] >> cfg.ipm.bev_w;
  fs["ipm"]["bev_height"] >> cfg.ipm.bev_h;
  if (!fs["ipm"]["roi_w_over_l"].empty()) fs["ipm"]["roi_w_over_l"] >> cfg.ipm.roi_w_over_l;

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
  fs["blsf"]["draw_thickness"] >> cfg.blsf.draw_thickness;

  fs["features"]["source"] >> cfg.feat_source;
  // Legacy keys are rejected, never silently reinterpreted.
  if (!fs["features"]["hybrid_or"].empty()) return false;
  if (!fs["blsf"]["min_dom_ratio"].empty()) return false;
  if (!fs["blsf"]["enabled"].empty()) {
    int enabled=1; fs["blsf"]["enabled"] >> enabled; cfg.blsf_enabled = enabled != 0;
  }

  fs["peaks"]["smooth_ksize"] >> cfg.peaks_smooth;
  fs["peaks"]["min_peak_value"] >> cfg.peaks_min;

  fs["tracker"]["n_windows"] >> cfg.n_windows;
  fs["tracker"]["margin"] >> cfg.margin;
  fs["tracker"]["minpix"] >> cfg.minpix;

  fs["ransac"]["iters"] >> cfg.ransac_iters;
  fs["ransac"]["inlier_thresh"] >> cfg.ransac_thresh;
  fs["ransac"]["min_inliers"] >> cfg.ransac_min_inliers;

  fs.release();
  cfg.blsf.min_len = cfg.lsd_min_len;
  return valid_blsf_config(cfg.blsf) && cfg.ipm.bev_w > 0 && cfg.ipm.bev_h > 0 &&
    std::isfinite(cfg.ipm.roi_w_over_l) && cfg.ipm.roi_w_over_l >= 0 &&
    cfg.mlt_k > 0 && cfg.n_windows > 0 && cfg.n_windows <= cfg.ipm.bev_h &&
    cfg.margin > 0 && cfg.minpix > 0 && cfg.peaks_smooth > 0 && cfg.peaks_min > 0 &&
    cfg.ransac_iters > 0 && cfg.ransac_thresh > 0 && cfg.ransac_min_inliers >= 3 &&
    (cfg.feat_source == "segments_mask" || cfg.feat_source == "binary_and_segments" || cfg.feat_source == "binary");
  } catch (const cv::Exception&) {
    return false;
  }
}

RunResult run_pipeline(const cv::Mat& bgr, Config& cfg, DebugPack& dbg) {
  RunResult rr;
  cfg.blsf.min_len = cfg.lsd_min_len;
  if (!valid_blsf_config(cfg.blsf) ||
      (cfg.feat_source != "segments_mask" && cfg.feat_source != "binary_and_segments" && cfg.feat_source != "binary")) {
    rr.status = "invalid_configuration";
    return rr;
  }

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
  if (cfg.blsf_enabled) blsf_filter(segs, segf, cfg.blsf, rr.vote);
  else segf = segs; // paired ablation, retaining the same LSD length rule
  dbg.seg_after = draw_segments(bin_bgr, segf, cv::Scalar(0,255,0), 2);

  if (rr.vote.low_confidence) {
    rr.status = "low_confidence";
    dbg.seg_mask = cv::Mat::zeros(dbg.binary.size(), CV_8U);
    dbg.feat_used = dbg.seg_mask.clone();
    cv::cvtColor(dbg.feat_used, dbg.windows_img, cv::COLOR_GRAY2BGR); // empty tracker input, no binary fallback
    dbg.overlay = dbg.bev_bgr.clone();
    return rr;
  }

  // 6) seg_mask + feature selection
  dbg.seg_mask = segments_mask(segf, dbg.binary.cols, dbg.binary.rows, cfg.blsf.draw_thickness);

  dbg.feat_used = select_features(dbg.binary, dbg.seg_mask, cfg.feat_source);
  cv::cvtColor(dbg.feat_used, dbg.windows_img, cv::COLOR_GRAY2BGR);

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
