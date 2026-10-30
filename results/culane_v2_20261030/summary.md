| Subset | Condition | Frames | P | R | F1 [95% CI] | Low-conf. |
|---|---|---|---|---|---|---|
| dazzle | with_blsf | 486 | 0.507 | 0.206 | 0.292 [0.256, 0.329] | 0.132 |
| dazzle | without_blsf | 486 | 0.403 | 0.236 | 0.297 [0.264, 0.332] | 0.000 |
| dazzle | delta F1 (with - without) | | | | [-0.025, +0.015] | McNemar p=0.18 |
| dazzle | with_blsf_eq6 | 486 | 0.465 | 0.177 | 0.256 [0.221, 0.291] | 0.132 |
| dazzle | delta F1 (with - with_blsf_eq6) | | | | [+0.017, +0.059] | McNemar p=0.0352 |
| night | with_blsf | 7029 | 0.690 | 0.364 | 0.477 [0.466, 0.488] | 0.158 |
| night | without_blsf | 7029 | 0.559 | 0.364 | 0.440 [0.430, 0.451] | 0.000 |
| night | delta F1 (with - without) | | | | [+0.032, +0.041] | McNemar p=1.66e-44 |
| night | with_blsf_eq6 | 7029 | 0.659 | 0.307 | 0.419 [0.408, 0.430] | 0.158 |
| night | delta F1 (with - with_blsf_eq6) | | | | [+0.053, +0.064] | McNemar p=1.22e-24 |
| curve | with_blsf | 422 | 0.580 | 0.227 | 0.327 [0.288, 0.367] | 0.137 |
| curve | without_blsf | 422 | 0.583 | 0.258 | 0.358 [0.317, 0.401] | 0.000 |
| curve | delta F1 (with - without) | | | | [-0.050, -0.014] | McNemar p=0.00342 |
| curve | with_blsf_eq6 | 422 | 0.622 | 0.239 | 0.345 [0.305, 0.388] | 0.137 |
| curve | delta F1 (with - with_blsf_eq6) | | | | [-0.036, -0.002] | McNemar p=0.0654 |
| normal | with_blsf | 9621 | 0.784 | 0.521 | 0.626 [0.618, 0.633] | 0.050 |
| normal | without_blsf | 9621 | 0.726 | 0.531 | 0.614 [0.605, 0.621] | 0.000 |
| normal | delta F1 (with - without) | | | | [+0.009, +0.016] | McNemar p=0.354 |
| normal | with_blsf_eq6 | 9621 | 0.768 | 0.500 | 0.606 [0.598, 0.614] | 0.050 |
| normal | delta F1 (with - with_blsf_eq6) | | | | [+0.016, +0.024] | McNemar p=0.000888 |
| all | with_blsf | 17558 | 0.745 | 0.447 | 0.559 [0.553, 0.565] | 0.098 |
| all | without_blsf | 17558 | 0.658 | 0.455 | 0.538 [0.532, 0.544] | 0.000 |
| all | delta F1 (with - without) | | | | [+0.019, +0.024] | McNemar p=6.11e-17 |
| all | with_blsf_eq6 | 17558 | 0.727 | 0.414 | 0.527 [0.521, 0.534] | 0.098 |
| all | delta F1 (with - with_blsf_eq6) | | | | [+0.029, +0.035] | McNemar p=1.91e-21 |

Secondary metric (image space, CULane-style 30 px, ego lanes, BEV ROI region):

| Subset | Condition | P | R | F1 [95% CI] |
|---|---|---|---|---|
| dazzle | with_blsf | 0.623 | 0.253 | 0.359 [0.320, 0.399] |
| dazzle | without_blsf | 0.489 | 0.286 | 0.361 [0.325, 0.399] |
| dazzle | delta F1 (with - without) | | | [-0.023, +0.019] |
| dazzle | with_blsf_eq6 | 0.586 | 0.223 | 0.323 [0.283, 0.363] |
| dazzle | delta F1 (with - with_blsf_eq6) | | | [+0.016, +0.061] |
| night | with_blsf | 0.744 | 0.392 | 0.514 [0.503, 0.525] |
| night | without_blsf | 0.623 | 0.405 | 0.491 [0.480, 0.501] |
| night | delta F1 (with - without) | | | [+0.018, +0.028] |
| night | with_blsf_eq6 | 0.717 | 0.334 | 0.455 [0.444, 0.467] |
| night | delta F1 (with - with_blsf_eq6) | | | [+0.053, +0.064] |
| curve | with_blsf | 0.702 | 0.275 | 0.395 [0.355, 0.437] |
| curve | without_blsf | 0.649 | 0.288 | 0.399 [0.359, 0.441] |
| curve | delta F1 (with - without) | | | [-0.020, +0.012] |
| curve | with_blsf_eq6 | 0.712 | 0.273 | 0.395 [0.354, 0.438] |
| curve | delta F1 (with - with_blsf_eq6) | | | [-0.012, +0.012] |
| normal | with_blsf | 0.836 | 0.555 | 0.667 [0.660, 0.674] |
| normal | without_blsf | 0.785 | 0.575 | 0.664 [0.656, 0.671] |
| normal | delta F1 (with - without) | | | [-0.000, +0.007] |
| normal | with_blsf_eq6 | 0.819 | 0.534 | 0.646 [0.638, 0.654] |
| normal | delta F1 (with - with_blsf_eq6) | | | [+0.017, +0.025] |
| all | with_blsf | 0.800 | 0.480 | 0.600 [0.594, 0.606] |
| all | without_blsf | 0.720 | 0.497 | 0.588 [0.582, 0.595] |
| all | delta F1 (with - without) | | | [+0.009, +0.014] |
| all | with_blsf_eq6 | 0.782 | 0.445 | 0.567 [0.561, 0.574] |
| all | delta F1 (with - with_blsf_eq6) | | | [+0.030, +0.036] |

Clip-cluster paired bootstrap (bev metric; primary intervals of protocol v2):

| Subset | Clips | Condition | F1 | 95% CI | Difference | 95% CI |
|---|---|---|---|---|---|---|
| dazzle | 48 | with_blsf | 0.292 | [0.164, 0.458] | | |
| dazzle | 48 | without_blsf | 0.297 | [0.161, 0.445] | | |
| dazzle | 48 | with_blsf_eq6 | 0.256 | [0.149, 0.408] | | |
| dazzle | | | | | with_blsf - without_blsf | [-0.034, +0.029] |
| dazzle | | | | | with_blsf - with_blsf_eq6 | [+0.003, +0.062] |
| night | 61 | with_blsf | 0.477 | [0.398, 0.550] | | |
| night | 61 | without_blsf | 0.440 | [0.366, 0.511] | | |
| night | 61 | with_blsf_eq6 | 0.419 | [0.346, 0.487] | | |
| night | | | | | with_blsf - without_blsf | [+0.025, +0.046] |
| night | | | | | with_blsf - with_blsf_eq6 | [+0.041, +0.078] |
| curve | 70 | with_blsf | 0.327 | [0.233, 0.417] | | |
| curve | 70 | without_blsf | 0.358 | [0.255, 0.464] | | |
| curve | 70 | with_blsf_eq6 | 0.345 | [0.243, 0.450] | | |
| curve | | | | | with_blsf - without_blsf | [-0.057, -0.006] |
| curve | | | | | with_blsf - with_blsf_eq6 | [-0.045, +0.001] |
| normal | 315 | with_blsf | 0.626 | [0.592, 0.657] | | |
| normal | 315 | without_blsf | 0.614 | [0.579, 0.645] | | |
| normal | 315 | with_blsf_eq6 | 0.606 | [0.571, 0.637] | | |
| normal | | | | | with_blsf - without_blsf | [+0.006, +0.018] |
| normal | | | | | with_blsf - with_blsf_eq6 | [+0.014, +0.027] |
| all | 380 | with_blsf | 0.559 | [0.521, 0.593] | | |
| all | 380 | without_blsf | 0.538 | [0.499, 0.573] | | |
| all | 380 | with_blsf_eq6 | 0.527 | [0.490, 0.562] | | |
| all | | | | | with_blsf - without_blsf | [+0.015, +0.027] |
| all | | | | | with_blsf - with_blsf_eq6 | [+0.024, +0.041] |

Clip-cluster paired bootstrap (image metric; primary intervals of protocol v2):

| Subset | Clips | Condition | F1 | 95% CI | Difference | 95% CI |
|---|---|---|---|---|---|---|
| dazzle | 48 | with_blsf | 0.359 | [0.204, 0.522] | | |
| dazzle | 48 | without_blsf | 0.361 | [0.204, 0.522] | | |
| dazzle | 48 | with_blsf_eq6 | 0.323 | [0.196, 0.469] | | |
| dazzle | | | | | with_blsf - without_blsf | [-0.028, +0.021] |
| dazzle | | | | | with_blsf - with_blsf_eq6 | [-0.002, +0.067] |
| night | 61 | with_blsf | 0.514 | [0.433, 0.588] | | |
| night | 61 | without_blsf | 0.491 | [0.414, 0.563] | | |
| night | 61 | with_blsf_eq6 | 0.455 | [0.380, 0.524] | | |
| night | | | | | with_blsf - without_blsf | [+0.011, +0.033] |
| night | | | | | with_blsf - with_blsf_eq6 | [+0.044, +0.074] |
| curve | 70 | with_blsf | 0.395 | [0.296, 0.497] | | |
| curve | 70 | without_blsf | 0.399 | [0.301, 0.500] | | |
| curve | 70 | with_blsf_eq6 | 0.395 | [0.298, 0.498] | | |
| curve | | | | | with_blsf - without_blsf | [-0.022, +0.014] |
| curve | | | | | with_blsf - with_blsf_eq6 | [-0.012, +0.011] |
| normal | 315 | with_blsf | 0.667 | [0.631, 0.698] | | |
| normal | 315 | without_blsf | 0.664 | [0.629, 0.695] | | |
| normal | 315 | with_blsf_eq6 | 0.646 | [0.610, 0.678] | | |
| normal | | | | | with_blsf - without_blsf | [-0.003, +0.009] |
| normal | | | | | with_blsf - with_blsf_eq6 | [+0.013, +0.029] |
| all | 380 | with_blsf | 0.600 | [0.561, 0.635] | | |
| all | 380 | without_blsf | 0.588 | [0.549, 0.625] | | |
| all | 380 | with_blsf_eq6 | 0.567 | [0.528, 0.603] | | |
| all | | | | | with_blsf - without_blsf | [+0.006, +0.017] |
| all | | | | | with_blsf - with_blsf_eq6 | [+0.024, +0.041] |
