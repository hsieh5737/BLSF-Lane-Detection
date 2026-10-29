#include <opencv2/opencv.hpp>
#include <iostream>
#include <string>
#include <vector>
#include "pipeline.h"
#include "utils.h"
#include "ipm.h"

using namespace blsf;

static void save_debug_pack(const std::string& debug_dir, const std::string& name, const DebugPack& d) {
  ensure_dir(debug_dir + "/" + name);
  cv::imwrite(debug_dir + "/" + name + "/01_bev.png", d.bev_bgr);
  cv::imwrite(debug_dir + "/" + name + "/02_gray.png", d.gray);
  cv::imwrite(debug_dir + "/" + name + "/03_median.png", d.median);
  cv::imwrite(debug_dir + "/" + name + "/04_binary.png", d.binary);
  cv::imwrite(debug_dir + "/" + name + "/05_seg_before.png", d.seg_before);
  cv::imwrite(debug_dir + "/" + name + "/06_seg_after.png", d.seg_after);
  cv::imwrite(debug_dir + "/" + name + "/07_seg_mask.png", d.seg_mask);
  cv::imwrite(debug_dir + "/" + name + "/08_feat_used.png", d.feat_used);
  cv::imwrite(debug_dir + "/" + name + "/09_windows.png", d.windows_img);
  cv::imwrite(debug_dir + "/" + name + "/10_overlay.png", d.overlay);

  // mosaic
  auto to3 = [](const cv::Mat& m){
    cv::Mat out;
    if (m.empty()) return out;
    if (m.channels()==1) cv::cvtColor(m, out, cv::COLOR_GRAY2BGR);
    else out = m;
    return out;
  };

  std::vector<cv::Mat> tiles = { to3(d.gray), to3(d.binary), to3(d.seg_mask), to3(d.windows_img), to3(d.overlay) };
  int w=320, h=240;
  for (auto& t : tiles) if (!t.empty()) cv::resize(t, t, cv::Size(w,h));
  cv::Mat row1, row2, mosaic;
  cv::hconcat(std::vector<cv::Mat>{tiles[0],tiles[1],tiles[2]}, row1);
  cv::hconcat(std::vector<cv::Mat>{tiles[3],tiles[4],tiles[4]}, row2);
  cv::vconcat(row1, row2, mosaic);
  cv::imwrite(debug_dir + "/" + name + "/00_mosaic.png", mosaic);
}

int main(int argc, char** argv) {
  std::string input_dir;
  std::string output_dir="outputs/run";
  std::string debug_dir="outputs/debug";
  std::string config_path="configs/default.yaml";
  bool reuse_h=false;

  for (int i=1;i<argc;++i) {
    std::string a = argv[i];
    if (a=="--input_dir" && i+1<argc) input_dir = argv[++i];
    else if (a=="--output_dir" && i+1<argc) output_dir = argv[++i];
    else if (a=="--debug_dir" && i+1<argc) debug_dir = argv[++i];
    else if (a=="--config" && i+1<argc) config_path = argv[++i];
    else if (a=="--reuse_h") reuse_h=true;
  }

  if (input_dir.empty()) {
    std::cerr << "Usage: blsf_lane --input_dir <folder> [--output_dir ...] [--debug_dir ...] [--config ...] [--reuse_h]\n";
    return 1;
  }

  Config cfg;
  if (!load_config_yaml(config_path, cfg)) {
    std::cerr << "Failed to load config: " << config_path << "\n";
    return 1;
  }

  ensure_dir(output_dir);
  ensure_dir(debug_dir);
  ensure_dir(output_dir + "/overlay");

  std::vector<std::string> images;
  if (!list_images(input_dir, images)) {
    std::cerr << "No images found in: " << input_dir << "\n";
    return 1;
  }

  std::string H_path = output_dir + "/homography.yml";
  if (reuse_h) {
    if (!load_homography(H_path, cfg.ipm)) {
      std::cerr << "reuse_h requested but homography not found: " << H_path << "\n";
      return 1;
    }
  } else {
    cv::Mat first = cv::imread(images[0]);
    if (first.empty()) { std::cerr << "Failed to read: " << images[0] << "\n"; return 1; }
    if (!pick_homography_ui(first, cfg.ipm)) {
      std::cerr << "Homography selection canceled.\n";
      return 1;
    }
    save_homography(H_path, cfg.ipm);
  }

  for (auto& path : images) {
    cv::Mat bgr = cv::imread(path);
    if (bgr.empty()) continue;

    DebugPack dbg;
    RunResult rr = run_pipeline(bgr, cfg, dbg);

    std::string name = basename_noext(path);
    cv::imwrite(output_dir + "/overlay/" + name + ".png", dbg.overlay);
    save_debug_pack(debug_dir, name, dbg);

    std::cout << name << " status=" << rr.status
              << " dom=" << rr.vote.dom << " dom_ratio=" << rr.vote.dom_ratio
              << " peaks=(" << rr.peaks.x_left << "," << rr.peaks.x_right << ")\n";
  }

  return 0;
}
