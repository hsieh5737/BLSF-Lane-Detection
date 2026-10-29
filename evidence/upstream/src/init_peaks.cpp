#include "init_peaks.h"
#include "utils.h"

namespace blsf {

Peaks find_initial_peaks(const cv::Mat& feat, int smooth_ksize, int min_peak_value) {
  CV_Assert(feat.type()==CV_8U);
  Peaks p;
  int W=feat.cols, H=feat.rows;
  int y0=H/2;

  cv::Mat hist = cv::Mat::zeros(1, W, CV_32S);
  for (int x=0;x<W;++x) {
    int sum=0;
    for (int y=y0;y<H;++y) sum += (feat.at<uchar>(y,x)>0) ? 1 : 0;
    hist.at<int>(0,x)=sum;
  }

  int k=ensure_odd(smooth_ksize);
  cv::Mat hf;
  hist.convertTo(hf, CV_32F);
  cv::blur(hf, hf, cv::Size(k,1));
  hf.convertTo(hist, CV_32S);

  int mid=W/2;
  int bestL=-1,bestR=-1,maxL=-1,maxR=-1;
  for (int x=0;x<mid;++x){ int v=hist.at<int>(0,x); if (v>maxL){maxL=v;bestL=x;} }
  for (int x=mid;x<W;++x){ int v=hist.at<int>(0,x); if (v>maxR){maxR=v;bestR=x;} }

  if (maxL>=min_peak_value) p.x_left=bestL;
  if (maxR>=min_peak_value) p.x_right=bestR;
  if (p.x_left>=0 && p.x_right>=0) p.lane_width=p.x_right-p.x_left;
  p.histogram=hist;
  return p;
}

} // namespace blsf
