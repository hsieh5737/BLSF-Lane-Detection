#include "pipeline.h"
#include "geometry.h"
#include "lsd.h"
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <functional>
#include <limits>
#include <filesystem>
#include <fstream>
#include <random>
#include <algorithm>

using namespace blsf;
static int passed=0;
static void check(bool c,const char* msg) { if(!c) throw std::runtime_error(msg); }
static Segment seg(float a,float len=300) {
  float r=a*CV_PI/180;
  return {200,450,200+len*std::sin(r),450-len*std::cos(r),len,a};
}
static void test(const char* n,const std::function<void()>& f) {
  f();++passed;std::cout << "PASS " << n << "\n";
}
static VoteInfo filter(const std::vector<Segment>& s,std::vector<Segment>& out,BLSFConfig c={}) {
  VoteInfo v;blsf_filter(s,out,c,v);return v;
}
int main(int argc,char** argv) {
 try {
  std::string root=argc>1?argv[1]:".";
  test("angle_vertical_both_orders",[]{check(vertical_angle_deg(0,-300)==0,"up");check(vertical_angle_deg(0,300)==0,"down");});
  test("angle_endpoint_invariance_sweep",[]{
    for(int a=-89;a<=89;++a){auto s=seg(a);float dx=s.x2-s.x1,dy=s.y2-s.y1;
      check(std::abs(vertical_angle_deg(dx,dy)-a)<0.001,"angle");check(std::abs(vertical_angle_deg(-dx,-dy)-a)<0.001,"reverse");}
  });
  test("horizontal_and_degenerate",[]{check(vertical_angle_deg(100,0)==-90,"horizontal");check(std::isnan(vertical_angle_deg(0,0)),"zero");check(std::isnan(vertical_angle_deg(NAN,1)),"nan");});
  test("vertical_overlap_and_straight_tie",[]{std::vector<Segment> o;auto v=filter({seg(0),seg(0)},o);
    check(o.size()==2 && !v.low_confidence && v.dom==1,"vertical");check(v.B0==600 && v.B1==600 && v.B2==600 && v.unique_vote==600 && v.dom_ratio==1,"unique votes");});
  test("strict_35_degree_envelope",[]{for(float a:{-35.f,35.f}){std::vector<Segment> o;auto v=filter({seg(a),seg(a)},o);check(o.size()==2&&!v.low_confidence,"inclusive edge");}
    for(float a:{-35.001f,35.001f,-90.f,80.f}){std::vector<Segment> o;auto v=filter({seg(a),seg(a)},o);check(o.empty()&&v.low_confidence,"outside");}});
  test("straight_band_edges_with_support",[]{std::vector<Segment> o;auto v=filter({seg(-5),seg(0),seg(5),seg(5.001f,21)},o);
    check(v.dom==1&&v.TL==-5&&v.TU==5&&o.size()==3,"straight range");});
  test("left_and_right_band_selection",[]{for(float a:{-25.f,25.f}){std::vector<Segment> o;auto v=filter({seg(a),seg(a),seg(0)},o);check(o.size()==3 && v.dom==(a<0?0:2),"band");}});
  test("length_boundary_strict",[]{BLSFConfig c;std::vector<Segment> o;c.min_total_vote=1;
    auto v=filter({seg(0,20)},o,c);check(o.empty()&&v.low_confidence,"len20");
    v=filter({seg(0,20.001f)},o,c);check(o.size()==1&&!v.low_confidence,"len20plus");});
  test("insufficient_unique_evidence",[]{std::vector<Segment> o;auto v=filter({seg(0,299)},o);check(o.empty()&&v.low_confidence,"299");});
  test("invalid_and_empty_evidence",[]{std::vector<Segment> o;auto v=filter({},o);check(o.empty()&&v.low_confidence,"empty");
    auto s=seg(0);s.theta_deg=NAN;v=filter({s},o);check(o.empty()&&v.low_confidence,"nan");});
  test("dominance_ratio_is_diagnostic_only",[]{std::mt19937 g(7);std::uniform_real_distribution<float> A(-35,35),L(21,200);std::uniform_int_distribution<int> N(1,40);
    BLSFConfig c;c.min_total_vote=1;for(int t=0;t<20000;++t){std::vector<Segment> s,o;int n=N(g);for(int i=0;i<n;++i)s.push_back(seg(A(g),L(g)));
      auto v=filter(s,o,c);check(v.dom_ratio>=0.5f-1e-6f&&!v.low_confidence,"A0 U A2 covers envelope, q>=0.5");}});
  test("evidence_gate_on_retained_support",[]{std::vector<Segment> o;auto v=filter({seg(-20,160),seg(20,150)},o);
    check(v.unique_vote==310&&v.retained_vote==160&&o.empty()&&v.low_confidence,"unique length alone must not pass");
    v=filter({seg(-20,310),seg(20,150)},o);float kept=0;for(auto&x:o)kept+=x.len;
    check(!v.low_confidence&&v.dom==0&&o.size()==1&&kept==v.retained_vote&&kept==310,"retained support equals winning bin");});
  test("envelope_fixed_at_35",[]{BLSFConfig c;check(valid_blsf_config(c),"35 ok");for(float m:{20.f,34.9f,35.1f,85.f}){c.max_abs_angle=m;check(!valid_blsf_config(c),"envelope must be exactly 35");}});
  test("legacy_ratio_key_rejected",[&]{auto t=std::filesystem::temp_directory_path()/"blsf_legacy_ratio.yaml";
    std::ifstream in(root+"/configs/default.yaml");std::string y((std::istreambuf_iterator<char>(in)),{});auto k=y.find("  min_total_vote:");check(k!=std::string::npos,"key");
    y.insert(k,"  min_dom_ratio: 0.40\n");std::ofstream(t)<<y;Config c;check(!load_config_yaml(t.string(),c),"min_dom_ratio rejected");std::filesystem::remove(t);});
  test("expansion_and_min_exclusion_rejected",[]{BLSFConfig c;c.delta_theta=12;check(!valid_blsf_config(c),"expansion");c.delta_theta=0;c.min_abs_angle=5;check(!valid_blsf_config(c),"min angle");});
  test("mask_is_binary",[]{auto m=segments_mask({seg(3)},640,480,2);cv::Mat bad=(m!=0)&(m!=255);check(cv::countNonZero(bad)==0,"mask");});
  test("feature_rejected_pixel_stays_removed",[]{cv::Mat b=cv::Mat::zeros(30,30,CV_8U),s=b.clone();b.at<uchar>(3,4)=255;s.at<uchar>(20,20)=255;
    auto f=select_features(b,s,"segments_mask");check(f.at<uchar>(3,4)==0&&f.at<uchar>(20,20)==255,"mask path");
    auto a=select_features(b,s,"binary_and_segments");check(cv::countNonZero(a)==0,"and");
    cv::Mat u;cv::bitwise_or(b,s,u);check(u.at<uchar>(3,4)==255,"or control");});
  test("synthetic_lsd_vertical",[]{cv::Mat b(480,640,CV_8U,cv::Scalar(0));cv::rectangle(b,{180,20},{186,460},cv::Scalar(255),-1);cv::rectangle(b,{450,20},{456,460},cv::Scalar(255),-1);
    std::vector<Segment> s,o;detect_segments_lsd(b,s,20);check(s.size()>=4,"LSD detections");for(auto x:s)check(std::abs(x.theta_deg)<0.1,"vertical LSD");
    auto v=filter(s,o);check(o.size()==s.size()&&!v.low_confidence,"all kept");std::cout << "DATA vertical_rectangles input=" << s.size() << " kept=" << o.size() << "\n";});
  test("configuration_and_paired_ablation",[&]{Config a,b;check(load_config_yaml(root+"/configs/default.yaml",a),"default config");check(load_config_yaml(root+"/configs/ablation_no_blsf.yaml",b),"ablation config");
    check(a.blsf_enabled&&!b.blsf_enabled&&a.feat_source==b.feat_source&&a.lsd_min_len==b.lsd_min_len&&a.mlt_k==b.mlt_k,"paired");
    check(!load_config_yaml(root+"/evidence/upstream/configs/default.yaml",a),"legacy rejected");});
  test("homography_size_must_match_config",[&]{std::string h=root+"/evidence/validation/synthetic_identity_homography.yml";
    IPM a;check(load_homography_matching(h,a)&&a.bev_w==640&&a.bev_h==480,"640x480 matches");
    IPM b;b.bev_w=225;b.bev_h=300;check(!load_homography_matching(h,b)&&b.bev_w==225&&b.bev_h==300&&b.H.empty(),"225x300 config rejects 640x480 homography");
    IPM c;check(!load_homography_matching(root+"/no_such_file.yml",c),"missing");});
  test("pipeline_blank_rejects_and_clears",[]{Config c;c.ipm.H=cv::Mat::eye(3,3,CV_64F);c.ipm.ready=true;DebugPack d;
    auto r=run_pipeline(cv::Mat::zeros(480,640,CV_8UC3),c,d);check(!r.ok&&r.status=="low_confidence"&&!r.left.valid&&!r.right.valid,"blank status");check(cv::countNonZero(d.feat_used)==0,"no fallback");
    cv::Mat w;cv::cvtColor(d.windows_img,w,cv::COLOR_BGR2GRAY);check(cv::countNonZero(w)==0,"debug view shows empty tracker input");});
  test("pipeline_synthetic_and_ablation",[]{Config c;c.ipm.H=cv::Mat::eye(3,3,CV_64F);c.ipm.ready=true;
    cv::Mat b=cv::Mat::zeros(480,640,CV_8UC3);cv::line(b,{180,20},{180,460},cv::Scalar(255,255,255),3);cv::line(b,{450,20},{450,460},cv::Scalar(255,255,255),3);
    DebugPack d;auto r=run_pipeline(b,c,d);check(r.ok,"full pipeline");
    check(cv::countNonZero(d.feat_used!=d.seg_mask)==0,"tracker uses segment support");
    c.blsf_enabled=false;DebugPack e;auto q=run_pipeline(b,c,e);check(q.ok,"ablation full pipeline");
    std::cout << "DATA full_pipeline left_c=" << r.left.c << " right_c=" << r.right.c << "\n";});
  std::cout << passed << " regression cases passed; OpenCV " << CV_VERSION << "\n";return 0;
 } catch(const std::exception& e) {std::cerr << "FAIL after " << passed << ": " << e.what() << "\n";return 1;}
}
