#include "utils.h"
#include <filesystem>
#include <algorithm>

namespace fs = std::filesystem;
namespace blsf {

bool ensure_dir(const std::string& path) {
  std::error_code ec;
  fs::create_directories(path, ec);
  return !ec;
}

std::string basename_noext(const std::string& path) {
  fs::path p(path);
  return p.stem().string();
}

static bool is_image_ext(const std::string& ext) {
  std::string e = ext;
  std::transform(e.begin(), e.end(), e.begin(), ::tolower);
  return (e==".png"||e==".jpg"||e==".jpeg"||e==".bmp"||e==".tif"||e==".tiff");
}

bool list_images(const std::string& dir, std::vector<std::string>& out) {
  out.clear();
  if (!fs::exists(dir)) return false;
  for (auto& entry : fs::directory_iterator(dir)) {
    if (!entry.is_regular_file()) continue;
    auto p = entry.path();
    if (is_image_ext(p.extension().string())) out.push_back(p.string());
  }
  std::sort(out.begin(), out.end());
  return !out.empty();
}

double deg2rad(double d){ return d * CV_PI / 180.0; }
double rad2deg(double r){ return r * 180.0 / CV_PI; }

} // namespace blsf
