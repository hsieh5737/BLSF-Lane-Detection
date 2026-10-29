#pragma once
#include <opencv2/opencv.hpp>
#include <string>
#include <vector>

namespace blsf {
inline int ensure_odd(int k) { return (k % 2 == 0) ? (k + 1) : k; }
bool list_images(const std::string& dir, std::vector<std::string>& out);
bool ensure_dir(const std::string& path);
std::string basename_noext(const std::string& path);
double deg2rad(double d);
double rad2deg(double r);
} // namespace blsf
