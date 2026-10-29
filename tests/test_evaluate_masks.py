import json,pathlib,subprocess,sys,tempfile,unittest
import cv2,numpy as np

SCRIPT=pathlib.Path(__file__).resolve().parents[1]/"scripts/evaluate_masks.py"
class MaskEvaluation(unittest.TestCase):
    def test_counts_and_empty(self):
        with tempfile.TemporaryDirectory() as d:
            d=pathlib.Path(d);p=d/"pred";g=d/"gt";p.mkdir();g.mkdir()
            x=np.array([[255,255],[0,0]],dtype=np.uint8)
            y=np.array([[255,0],[255,0]],dtype=np.uint8)
            for folder,img in [(p,x),(g,y)]:
                cv2.imwrite(str(folder/"one.png"),img);cv2.imwrite(str(folder/"empty.png"),np.zeros_like(img))
            r=subprocess.run([sys.executable,str(SCRIPT),"--predictions",str(p),"--ground_truth",str(g),"--output",str(d/"score.json")],capture_output=True)
            self.assertEqual(r.returncode,0,r.stderr)
            s=json.loads((d/"score.json").read_text());self.assertEqual((s["tp"],s["fp"],s["fn"]),(1,1,1))
            self.assertEqual(s["f1"],0.5);self.assertAlmostEqual(s["iou"],1/3);self.assertEqual(s["both_empty_frames"],1)
    def test_missing_frame_fails(self):
        with tempfile.TemporaryDirectory() as d:
            d=pathlib.Path(d);p=d/"pred";g=d/"gt";p.mkdir();g.mkdir()
            cv2.imwrite(str(p/"one.png"),np.zeros((2,2),np.uint8))
            r=subprocess.run([sys.executable,str(SCRIPT),"--predictions",str(p),"--ground_truth",str(g),"--output",str(d/"score.json")],capture_output=True)
            self.assertNotEqual(r.returncode,0)
if __name__=="__main__":unittest.main()
