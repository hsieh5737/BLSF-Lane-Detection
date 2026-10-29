# Running on Windows (MSYS2 UCRT64)

1. Install MSYS2 and open the **UCRT64** shell, then:

   ```bash
   pacman -Syu
   pacman -S --needed git mingw-w64-ucrt-x86_64-gcc mingw-w64-ucrt-x86_64-cmake \
     mingw-w64-ucrt-x86_64-ninja mingw-w64-ucrt-x86_64-opencv \
     mingw-w64-ucrt-x86_64-python mingw-w64-ucrt-x86_64-python-numpy \
     mingw-w64-ucrt-x86_64-python-opencv
   ```

2. Use **ASCII-only paths** for the repository, the dataset and the work
   directory (for example `D:/blsf/BLSF-Lane-Detection`, `D:/datasets/CULane`).
   OpenCV built with MinGW cannot open files whose paths contain non-ASCII
   characters, and `run_experiment.py` refuses such paths.

3. Build and test:

   ```bash
   cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
   cmake --build build
   ctest --test-dir build --output-on-failure
   python -m unittest discover -s tests -p 'test_*.py'
   ```

   The binary is `build/blsf_lane.exe`.

4. Run the experiment from the same UCRT64 shell (so the OpenCV DLLs are on
   `PATH`), following README *Pre-registered experiment*.
