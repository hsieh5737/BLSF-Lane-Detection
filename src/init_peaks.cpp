#include "init_peaks.h"
#include "utils.h"
#include <cmath>
#include <vector>

namespace blsf {

Peaks find_initial_peaks(const cv::Mat& feat, int smooth_ksize, int min_peak_value, const PeakOptions& opt) {
  CV_Assert(feat.type()==CV_8U);
  Peaks p;
  int W=feat.cols, H=feat.rows;
  double rf = std::min(1.0, std::max(0.0, opt.rows_fraction));
  int y0 = (rf == 0.5) ? H/2 : std::max(0, std::min(H-1, (int)std::lround(H*(1.0-rf))));

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
  auto in_range = [&](int x){ return (opt.max_offset<=0 || std::abs(x-mid) <= opt.max_offset) && std::abs(x-mid) >= opt.min_offset; };
  if (opt.select == "nearest_expected") {
    // local maxima (plateaus count once) at or above the threshold; the one whose
    // offset from the BEV centre is closest to the expected ego half width wins.
    auto cands = [&](int lo, int hi) {
      std::vector<std::pair<int,int>> c;  // (x, value)
      for (int x=lo;x<hi;++x) {
        int v=hist.at<int>(0,x);
        if (v<min_peak_value || !in_range(x)) continue;
        int vl = x>0 ? hist.at<int>(0,x-1) : -1;
        int vr = x+1<W ? hist.at<int>(0,x+1) : -1;
        if (v<vl || v<vr || v==vl) continue;  // first column of a plateau only
        int e=x; while (e+1<W && hist.at<int>(0,e+1)==v) ++e;
        if (e+1<W && hist.at<int>(0,e+1)>v) continue;
        c.push_back({(x+e)/2, v});
      }
      return c;
    };
    auto dev = [&](int x){ return std::abs(std::abs(x-mid)-opt.expected_offset); };
    auto CL=cands(0,mid), CR=cands(mid,W);
    int bl=-1, br=-1;
    for (auto& c: CL) if (bl<0 || dev(c.first)<dev(CL[bl].first)) bl=&c-&CL[0];
    for (auto& c: CR) if (br<0 || dev(c.first)<dev(CR[br].first)) br=&c-&CR[0];
    if (opt.max_width>0 && !CL.empty() && !CR.empty()) {
      // best admissible pair by total deviation from the expected positions
      int pl=-1, pr=-1, best=1<<30;
      for (size_t i=0;i<CL.size();++i) for (size_t j=0;j<CR.size();++j) {
        int w=CR[j].first-CL[i].first;
        if (w<opt.min_width || w>opt.max_width) continue;
        int d=dev(CL[i].first)+dev(CR[j].first);
        if (d<best) { best=d; pl=(int)i; pr=(int)j; }
      }
      if (pl>=0) { bl=pl; br=pr; }
      else if (CL[bl].second >= CR[br].second) br=-1;  // no admissible pair: keep the stronger side only
      else bl=-1;
    }
    p.x_left = bl>=0 ? CL[bl].first : -1;
    p.x_right = br>=0 ? CR[br].first : -1;
  } else {
    int bestL=-1,bestR=-1,maxL=-1,maxR=-1;
    for (int x=0;x<mid;++x){ if (!in_range(x)) continue; int v=hist.at<int>(0,x); if (v>maxL){maxL=v;bestL=x;} }
    for (int x=mid;x<W;++x){ if (!in_range(x)) continue; int v=hist.at<int>(0,x); if (v>maxR){maxR=v;bestR=x;} }
    if (maxL>=min_peak_value) p.x_left=bestL;
    if (maxR>=min_peak_value) p.x_right=bestR;
  }
  if (p.x_left>=0 && p.x_right>=0) p.lane_width=p.x_right-p.x_left;
  p.histogram=hist;
  return p;
}

} // namespace blsf
