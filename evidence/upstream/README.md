
---

# BLSF Lane Detection

Real-Time Deterministic Lane Detection on CPU-Only Embedded Systems via Binary Line Segment Filtering

This repository provides the official C++ implementation of the paper Real-Time Deterministic Lane Detection on CPU-Only Embedded Systems via Binary Line Segment Filtering.
Binary Line Segment Filtering (BLSF) is a lightweight lane detection algorithm specifically designed for CPU-only embedded systems, and it demonstrates strong robustness under challenging visual conditions, including strong backlighting, heavy rain, nighttime scenarios, and low-contrast road environments.

The implementation is developed with explainability and real-time determinism as the primary design goals.
By avoiding computationally expensive and latency-unpredictable deep learning models, the system is well suited for deployment on resource-constrained on-board computers, such as ARM-based platforms.

---

## Key Features


  **Pure CPU:** No GPU or AI accelerator is required.  
  The system can achieve 30+ FPS on ARM 2 GHz-class platforms, depending on resolution and configuration.


  **Robust:** Designed and validated for challenging scenarios, including strong backlight, nighttime driving, rain, fog, and low-contrast road conditions.


  **Explainable:** Based on geometric structures and line-segment-level filtering (Binary Line Segment Filtering),
  rather than black-box deep learning models.
  The detection behavior is analyzable, debuggable, and predictable.


  **Deterministic:** The computational pipeline and memory usage are fixed and well-bounded,
  making the approach suitable for safety-critical embedded systems.

---

## Implementation Notes

The project is implemented in C-style C++(`struct + function`) to ensure clarity and deterministic behavior.
Since OpenCV 4+ has removed the legacy C API (IplImage / cv),
a C++ compiler (g++ / clang++) is required to link against the OpenCV C++ interface.
The implementation targets on-board / embedded Linux environments and does not rely on GPU, CUDA, or deep learning frameworks.

---

## Build

```bash
mkdir -p build
cd build
cmake ..
cmake --build . -j
```

For embedded platforms, building in Release mode (e.g., with `-O3`) is strongly recommended to achieve optimal performance.

---

## Run (Image Folder)

```bash
./blsf_lane --input_dir ../data_images --output_dir ../outputs/run --debug_dir ../outputs/debug
```

### Homography / IPM Setup

During the first execution, the program opens a window on the first image and prompts the user to select four points to establish the IPM (Inverse Perspective Mapping):

1. Top-left
2. Top-right
3. Bottom-right
4. Bottom-left

* Press Enter to confirm
* Press r to reselect the points
* Press Esc to cancel

The generated homography will be saved as:

```
output_dir/homography.yml
```

For subsequent runs, the homography can be reused by running:

```bash
./blsf_lane --reuse_h
```

This is recommended for on-board deployment, where interactive GUI operations are often undesirable or unavailable.

---

## Citation

If you use this codebase or refer to our research in your work, please cite the following paper:

```bibtex
@article{tsai2025blsf,
  title={Real-Time Deterministic Lane Detection on CPU-Only Embedded Systems via Binary Line Segment Filtering},
  author={Tsai, Shang-En and Yang, Shih-Ming and Hsieh, Chia-Han},
  journal={Electronics},
  year={2025},
  note={In Press}
}
```

---

