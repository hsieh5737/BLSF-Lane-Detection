cmake_minimum_required(VERSION 3.16)

# Project name (CMake does NOT allow spaces)
project(BLSF_Lane_Detection LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Default to Release if not specified (important on ARM)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

find_package(OpenCV REQUIRED)

# Executable name (this is the actual binary name)
add_executable(blsf_lane
  src/main.cpp
  src/pipeline.cpp
  src/pipeline.h
  src/ipm.cpp
  src/ipm.h
  src/preprocess.cpp
  src/preprocess.h
  src/mlt.cpp
  src/mlt.h
  src/lsd.cpp
  src/lsd.h
  src/blsf.cpp
  src/blsf.h
  src/init_peaks.cpp
  src/init_peaks.h
  src/tracker.cpp
  src/tracker.h
  src/ransac_fit.cpp
  src/ransac_fit.h
  src/visualize.cpp
  src/visualize.h
  src/utils.cpp
  src/utils.h
)

target_include_directories(blsf_lane PRIVATE
  ${OpenCV_INCLUDE_DIRS}
  src
)

target_link_libraries(blsf_lane PRIVATE
  ${OpenCV_LIBS}
)

# --- Performance flags (safe defaults for ARM / embedded) ---
target_compile_options(blsf_lane PRIVATE
  -O3
  -DNDEBUG
)

# Optional: reduce binary size / improve determinism
# Comment out if any dependency requires RTTI / exceptions
target_compile_options(blsf_lane PRIVATE
  -fno-exceptions
  -fno-rtti
)

# Optional: ARM tuning
# Use ONLY when compiling directly on the target device
# target_compile_options(blsf_lane PRIVATE -mcpu=native)

# Some older toolchains may require explicit filesystem linking
# Uncomment only if linker errors occur
# target_link_libraries(blsf_lane PRIVATE stdc++fs)

# Embedded-friendly RPATH behavior
set_target_properties(blsf_lane PROPERTIES
  BUILD_RPATH_USE_ORIGIN ON
)
