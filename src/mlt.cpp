#include "mlt.h"
#include "utils.h"

// Paper-style: 1D median per row along x using rolling histogram (0..255).
namespace blsf {

static inline int median_from_hist(const int hist[256], int window) {
  int acc=0;
  int mid=(window+1)/2;
  for (int v=0; v<256; ++v) { acc += hist[v]; if (acc>=mid) return v; }
  return 0;
}

void mlt_binarize(const cv::Mat& gray, cv::Mat& binary, cv::Mat& median, int median_ksize, int offset_t) {
  CV_Assert(gray.type()==CV_8U);
  int k = ensure_odd(median_ksize);
  int pad = k/2;
  int W = gray.cols, H = gray.rows;

  median = cv::Mat(gray.size(), CV_8U);
  binary = cv::Mat(gray.size(), CV_8U);

  for (int y=0; y<H; ++y) {
    const uchar* row = gray.ptr<uchar>(y);
    int hist[256] = {0};

    // init for x=0 with edge-replicate
    for (int dx=-pad; dx<=pad; ++dx) {
      int xx = std::min(std::max(dx, 0), W-1);
      hist[row[xx]]++;
    }

    for (int x=0; x<W; ++x) {
      int m = median_from_hist(hist, k);
      median.at<uchar>(y,x) = (uchar)m;
      int thr = m + offset_t;
      binary.at<uchar>(y,x) = (row[x] > thr) ? 255 : 0;

      int x_out = x - pad;
      int x_in  = x + pad + 1;
      int xx_out = std::min(std::max(x_out, 0), W-1);
      int xx_in  = std::min(std::max(x_in, 0), W-1);
      hist[row[xx_out]]--;
      hist[row[xx_in]]++;
    }
  }
}

} // namespace blsf
