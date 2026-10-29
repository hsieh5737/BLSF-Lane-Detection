#include "preprocess.h"
namespace blsf {
cv::Mat weighted_gray(const cv::Mat& bgr, double w_r, double w_g, double w_b) {
  CV_Assert(bgr.type() == CV_8UC3);
  std::vector<cv::Mat> ch;
  cv::split(bgr, ch); // B,G,R
  cv::Mat fB, fG, fR;
  ch[0].convertTo(fB, CV_32F);
  ch[1].convertTo(fG, CV_32F);
  ch[2].convertTo(fR, CV_32F);
  cv::Mat grayf = w_b * fB + w_g * fG + w_r * fR;
  cv::Mat gray;
  grayf.convertTo(gray, CV_8U);
  return gray;
}
} // namespace blsf
