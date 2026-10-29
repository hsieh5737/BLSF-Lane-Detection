Synthetic pre-registration check: 16 frames per scene, BEV 225x300 on 11.25 x 15 m, F1 (ego lanes, IoU>=0.5, width 10 px).

| Scene | as configured with / without | proportional min_peak 31 with / without |
|---|---|---|
| straight, 2/4 m dashes | 1.000 / 1.000 | 0.000 / 0.000 |
| straight, 4/6 m dashes | 1.000 / 1.000 | 0.000 / 0.000 |
| straight, 6/9 m dashes | 0.938 / 0.938 | 0.938 / 0.938 |
| straight, 6/9 m, crosswalk | 0.938 / 0.938 | 0.000 / 0.000 |
| right curve k=0.012, 2/4 m | 0.935 / 0.935 | 0.000 / 0.000 |
| right curve k=0.012, 6/9 m | 0.562 / 0.562 | 0.000 / 0.000 |
| left curve k=-0.008, 6/9 m, crosswalk | 0.500 / 0.500 | 0.000 / 0.000 |
