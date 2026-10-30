#include "pipeline.h"
#include <cmath>
#include <algorithm>
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
  if (!fs["ipm"]["preblur"].empty()) fs["ipm"]["preblur"] >> cfg.ipm.preblur;
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
  if (!fs["blsf"]["strips"].empty()) fs["blsf"]["strips"] >> cfg.blsf_strips;
  if (!fs["blsf"]["gate"].empty()) fs["blsf"]["gate"] >> cfg.blsf.gate;
  if (!fs["blsf"]["decision"].empty()) fs["blsf"]["decision"] >> cfg.blsf.decision;

  fs["features"]["source"] >> cfg.feat_source;
  // Legacy keys are rejected, never silently reinterpreted.
  if (!fs["features"]["hybrid_or"].empty()) return false;
  if (!fs["blsf"]["min_dom_ratio"].empty()) return false;
  if (!fs["blsf"]["enabled"].empty()) {
    int enabled=1; fs["blsf"]["enabled"] >> enabled; cfg.blsf_enabled = enabled != 0;
  }

  fs["peaks"]["smooth_ksize"] >> cfg.peaks_smooth;
  fs["peaks"]["min_peak_value"] >> cfg.peaks_min;
  if (!fs["peaks"]["rows_fraction"].empty()) fs["peaks"]["rows_fraction"] >> cfg.peak_opt.rows_fraction;
  if (!fs["peaks"]["select"].empty()) fs["peaks"]["select"] >> cfg.peak_opt.select;
  if (!fs["peaks"]["expected_offset"].empty()) fs["peaks"]["expected_offset"] >> cfg.peak_opt.expected_offset;
  if (!fs["peaks"]["max_offset"].empty()) fs["peaks"]["max_offset"] >> cfg.peak_opt.max_offset;
  if (!fs["tracker"]["require_both_peaks"].empty()) {
    int rb=1; fs["tracker"]["require_both_peaks"] >> rb; cfg.require_both_peaks = rb != 0;
  }

  fs["tracker"]["n_windows"] >> cfg.n_windows;
  fs["tracker"]["margin"] >> cfg.margin;
  fs["tracker"]["minpix"] >> cfg.minpix;

  fs["ransac"]["iters"] >> cfg.ransac_iters;
  fs["ransac"]["inlier_thresh"] >> cfg.ransac_thresh;
  fs["ransac"]["min_inliers"] >> cfg.ransac_min_inliers;
  if (!fs["ransac"]["max_abs_a"].empty()) fs["ransac"]["max_abs_a"] >> cfg.ransac_max_abs_a;
  if (!fs["pair"].empty()) {
    if (!fs["pair"]["mode"].empty()) fs["pair"]["mode"] >> cfg.pair_mode;
    if (!fs["pair"]["min_width"].empty()) fs["pair"]["min_width"] >> cfg.pair_min_width;
    if (!fs["pair"]["max_width"].empty()) fs["pair"]["max_width"] >> cfg.pair_max_width;
    if (!fs["pair"]["max_width_change"].empty()) fs["pair"]["max_width_change"] >> cfg.pair_max_width_change;
  }
  if (!fs["accept"].empty()) {
    if (!fs["accept"]["min_inlier_frac"].empty()) fs["accept"]["min_inlier_frac"] >> cfg.accept_min_frac;
    if (!fs["accept"]["min_inlier_frac_single"].empty()) fs["accept"]["min_inlier_frac_single"] >> cfg.accept_min_frac_single;
  }
  if (!fs["ransac"]["linear_span"].empty()) fs["ransac"]["linear_span"] >> cfg.ransac_linear_span;
  if (!fs["ransac"]["refit"].empty()) { int rf=0; fs["ransac"]["refit"] >> rf; cfg.ransac_refit = rf != 0; }
  if (!fs["peaks"]["min_offset"].empty()) fs["peaks"]["min_offset"] >> cfg.peak_opt.min_offset;
  if (!fs["peaks"]["min_width"].empty()) fs["peaks"]["min_width"] >> cfg.peak_opt.min_width;
  if (!fs["peaks"]["max_width"].empty()) fs["peaks"]["max_width"] >> cfg.peak_opt.max_width;

  fs.release();
  cfg.blsf.min_len = cfg.lsd_min_len;
  return valid_blsf_config(cfg.blsf) && cfg.ipm.bev_w > 0 && cfg.ipm.bev_h > 0 &&
    std::isfinite(cfg.ipm.roi_w_over_l) && cfg.ipm.roi_w_over_l >= 0 &&
    cfg.mlt_k > 0 && cfg.n_windows > 0 && cfg.n_windows <= cfg.ipm.bev_h &&
    cfg.margin > 0 && cfg.minpix > 0 && cfg.peaks_smooth > 0 && cfg.peaks_min > 0 &&
    (cfg.pair_mode == "none" || cfg.pair_mode == "check" || cfg.pair_mode == "joint") &&
    cfg.blsf_strips >= 1 && cfg.blsf_strips <= 8 &&
    cfg.peak_opt.rows_fraction > 0 && cfg.peak_opt.rows_fraction <= 1 &&
    (cfg.peak_opt.select == "max" || cfg.peak_opt.select == "nearest_expected") &&
    cfg.peak_opt.expected_offset >= 0 && cfg.peak_opt.max_offset >= 0 && cfg.peak_opt.min_offset >= 0 &&
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
  if (cfg.blsf_enabled) {
    blsf_filter(segs, segf, cfg.blsf, rr.vote);  // whole-frame votes: confidence gate and diagnostics
    if (cfg.blsf_strips > 1 && !rr.vote.low_confidence) {
      // Per-strip band selection with the same bands and decision rule: on a curve
      // the near strip can stay straight while the far strip selects a curve band.
      // The confidence gate is the whole-frame one above; strips are not gated.
      BLSFConfig sc = cfg.blsf; sc.min_total_vote = 1e-3f;
      std::vector<std::vector<Segment>> by(cfg.blsf_strips);
      int Hb = cfg.ipm.bev_h;
      for (const auto& s : segs) {
        double ym = 0.5 * (s.y1 + s.y2);
        int k = (int)std::floor((Hb - 1 - ym) * cfg.blsf_strips / Hb);  // 0 = nearest strip
        by[std::max(0, std::min(cfg.blsf_strips - 1, k))].push_back(s);
      }
      segf.clear();
      for (auto& part : by) {
        std::vector<Segment> kept; VoteInfo vi;
        blsf_filter(part, kept, sc, vi);
        segf.insert(segf.end(), kept.begin(), kept.end());
      }
    }
  }
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
  rr.peaks = find_initial_peaks(dbg.feat_used, cfg.peaks_smooth, cfg.peaks_min, cfg.peak_opt);
  bool missing = cfg.require_both_peaks ? (rr.peaks.x_left < 0 || rr.peaks.x_right < 0)
                                        : (rr.peaks.x_left < 0 && rr.peaks.x_right < 0);
  if (missing) {
    rr.status = "no_peaks";
    dbg.overlay = dbg.bev_bgr.clone();
    return rr;
  }

  // 8) windows
  TrackResult tr = sliding_window_track(dbg.feat_used, rr.peaks, cfg.n_windows, cfg.margin, cfg.minpix);
  cv::Mat feat_bgr; cv::cvtColor(dbg.feat_used, feat_bgr, cv::COLOR_GRAY2BGR);
  dbg.windows_img = draw_windows(feat_bgr, tr);

  // 9) RANSAC
  auto left_fit  = fit_parabola_ransac(tr.pts_left,  cfg.ransac_iters, cfg.ransac_thresh, cfg.ransac_min_inliers,
                                         cfg.ransac_max_abs_a, cfg.ransac_refit,
                                         (int)std::lround(cfg.ransac_linear_span * cfg.ipm.bev_h));
  auto right_fit = fit_parabola_ransac(tr.pts_right, cfg.ransac_iters, cfg.ransac_thresh, cfg.ransac_min_inliers,
                                         cfg.ransac_max_abs_a, cfg.ransac_refit,
                                         (int)std::lround(cfg.ransac_linear_span * cfg.ipm.bev_h));
  rr.left = left_fit.poly;
  rr.right = right_fit.poly;
  auto stats = [](const RansacResult& f, const std::vector<cv::Point>& pts, int hits) {
    RunResult::SideStats st; st.inliers=f.inliers; st.npts=(int)pts.size(); st.hits=hits;
    int lo=1<<30, hi=-1;
    for (size_t i=0;i<f.inlier_mask.size();++i) if (f.inlier_mask[i]) { lo=std::min(lo,pts[i].y); hi=std::max(hi,pts[i].y); }
    st.span = hi>=0 ? hi-lo : 0;
    return st;
  };
  rr.left_st = stats(left_fit, tr.pts_left, tr.hits_left);
  rr.right_st = stats(right_fit, tr.pts_right, tr.hits_right);

  // 10) v2: pair consistency in the metric BEV (parallel boundaries, plausible width)
  auto frac = [](const RunResult::SideStats& st){ return st.npts>0 ? (double)st.inliers/st.npts : 0.0; };
  if (cfg.pair_mode != "none" && rr.left.valid && rr.right.valid) {
    double H=cfg.ipm.bev_h-1;
    double wb=eval_poly_x(rr.right,H)-eval_poly_x(rr.left,H), wt=eval_poly_x(rr.right,0)-eval_poly_x(rr.left,0);
    bool consistent = wb>=cfg.pair_min_width && wb<=cfg.pair_max_width && wt>=cfg.pair_min_width && wt<=cfg.pair_max_width &&
                      std::abs(wt-wb) <= cfg.pair_max_width_change;
    if (!consistent) {
      if (frac(rr.left_st) >= frac(rr.right_st)) rr.right.valid=false; else rr.left.valid=false;
    } else if (cfg.pair_mode == "joint") {
      // shared a, b; separate offsets: x = a y^2 + b y + c_side
      std::vector<std::pair<cv::Point,int>> P;
      for (size_t i=0;i<left_fit.inlier_mask.size();++i) if (left_fit.inlier_mask[i]) P.push_back({tr.pts_left[i],0});
      for (size_t i=0;i<right_fit.inlier_mask.size();++i) if (right_fit.inlier_mask[i]) P.push_back({tr.pts_right[i],1});
      bool linear = rr.left.a==0 && rr.right.a==0;
      int nc = linear ? 3 : 4;
      cv::Mat A((int)P.size(), nc, CV_64F, cv::Scalar(0)), X((int)P.size(), 1, CV_64F);
      for (int r=0;r<(int)P.size();++r) {
        double y=P[r].first.y; int c=0;
        if (!linear) A.at<double>(r,c++)=y*y;
        A.at<double>(r,c++)=y; A.at<double>(r,c+P[r].second)=1; X.at<double>(r,0)=P[r].first.x;
      }
      cv::Mat sol;
      if ((int)P.size()>=nc && cv::solve(A, X, sol, cv::DECOMP_SVD)) {
        double a = linear ? 0 : sol.at<double>(0,0), b = sol.at<double>(linear?0:1,0);
        if (!(cfg.ransac_max_abs_a>0 && std::abs(a)>cfg.ransac_max_abs_a)) {
          rr.left.a=a; rr.left.b=b; rr.left.c=sol.at<double>(nc-2,0);
          rr.right.a=a; rr.right.b=b; rr.right.c=sol.at<double>(nc-1,0);
        }
      }
    }
  }
  // 11) v2: per-side acceptance by inlier fraction (stricter for a side without partner)
  if (cfg.accept_min_frac>0 || cfg.accept_min_frac_single>0) {
    bool lv=rr.left.valid, rv=rr.right.valid;
    if (lv && frac(rr.left_st) < (rv ? cfg.accept_min_frac : cfg.accept_min_frac_single)) rr.left.valid=false;
    if (rv && frac(rr.right_st) < (lv ? cfg.accept_min_frac : cfg.accept_min_frac_single)) rr.right.valid=false;
  }

  rr.ok = rr.left.valid && rr.right.valid;
  if (rr.ok) rr.status = "ok";
  else if (!cfg.require_both_peaks && (rr.left.valid || rr.right.valid)) rr.status = "partial";
  else rr.status = "fit_failed";

  dbg.overlay = draw_polys(dbg.bev_bgr, rr.left, rr.right);
  return rr;
}

} // namespace blsf
