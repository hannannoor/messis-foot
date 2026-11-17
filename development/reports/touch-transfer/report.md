# Touch transfer and decoder restart results — 11 November 2026

Fixed protocol: [touch-transfer-protocol.md](../../docs/touch-transfer-protocol.md).

Starting state matched: clean branch `codex/stoppage-regime-2026-11-10`, head `5147e23`. Work branch: `codex/touch-transfer-2026-11-10`. No predictor sources changed.

90 variant scores and five additional natural-control reproduction checks were performed in one run. All 15 natural controls and all 15 stoppage-regime comparison values reproduced within 1e-9.

## Tracking profile

Provider ranges below use natural tracks. All provided-track information is bounded aggregates.

| Track | Observed share | Speed m/s | Surprise m/s | Owned/min visible | Surprise ≥3 share | Remote peak share | Bonus frames/owned touch |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Provided | 0.584179 | 5.108300 | 1.126769 | 10.457861 | 0.155712 | 0.297080 | 96.377125 |
| skillcorner (n=10) | 0.525990–0.643804 | 4.708561–5.217943 | 1.062871–1.201334 | 18.007388–21.637317 | 0.150967–0.175843 | 0.197628–0.231284 | 55.313980–61.575855 |
| dfl (n=4) | 1.000000–1.000000 | 0.000000–1.585172 | 0.000000–0.200539 | 17.501858–19.617192 | 0.089603–0.111106 | 0.090788–0.136697 | 45.627598–49.993754 |
| wcsf (n=1) | 1.000000–1.000000 | 1.592804–1.592804 | 0.112062–0.112062 | 21.271552–21.271552 | 0.121253–0.121253 | 0.129058–0.129058 | 43.945428–43.945428 |

S* = 1.126768830; R* = 10.457861445. All profile stop checks passed.

| DFL/WCSF scored track | Median surprise m/s |
| --- | --- |
| dfl-J03WN1 | 1.066647 |
| dfl-J03WOH | 1.062326 |
| dfl-J03WOY | 1.039035 |
| dfl-J03WR9 | 1.081570 |
| wcsf-used-match | 1.146687 |

## Group means

C = candidate; T = candidate+touch; thin = candidate+touch-thin; R = candidate+reset; TR = candidate+touch+reset. DFL/WCSF primary weights are WN1 .25, WR9 .25, WCSF .5. SkillCorner means weight each match equally. Mean spell counts are descriptive means, not pooled metric calculations.

### dfl_wcsf_primary

| Variant | Spell F1 | Macro F1 | Dead recall | Predicted spells | Reference spells |
| --- | --- | --- | --- | --- | --- |
| control | 0.343783 | 0.379501 | 0.000000 | 275.750000 | 423.000000 |
| candidate | 0.401270 | 0.704968 | 0.666551 | 355.000000 | 423.000000 |
| candidate+touch | 0.477651 | 0.722708 | 0.666551 | 397.250000 | 423.000000 |
| candidate+touch-thin | 0.398301 | 0.704760 | 0.666551 | 332.250000 | 423.000000 |
| candidate+reset | 0.418409 | 0.706565 | 0.666551 | 333.250000 | 423.000000 |
| candidate+touch+reset | 0.490677 | 0.723832 | 0.666551 | 379.000000 | 423.000000 |

| Touch Δ | Thin Δ | Reset Δ | Touch-reset Δ | Owned rate | Thinned rate | Bonus share | Thinned bonus share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.076381 | -0.002969 | 0.017139 | 0.013026 | 29.027399 | 10.423521 | 0.396491 | 0.328005 |

| Reset variant | Graded changed share | Owner agreement without | Owner agreement with |
| --- | --- | --- | --- |
| candidate+reset | 0.002899 | 0.445530 | 0.586279 |
| candidate+touch+reset | 0.002348 | 0.397297 | 0.526040 |

### skillcorner_confirmation

| Variant | Spell F1 | Macro F1 | Dead recall | Predicted spells | Reference spells |
| --- | --- | --- | --- | --- | --- |
| control | 0.586912 | 0.570955 | — | 350.600000 | 267.000000 |
| candidate | 0.584341 | 0.570137 | — | 345.400000 | 267.000000 |
| candidate+touch | 0.583469 | 0.569709 | — | 350.800000 | 267.000000 |
| candidate+touch-thin | 0.570125 | 0.561535 | — | 315.400000 | 267.000000 |
| candidate+reset | 0.584341 | 0.570137 | — | 345.400000 | 267.000000 |
| candidate+touch+reset | 0.583469 | 0.569709 | — | 350.800000 | 267.000000 |

| Touch Δ | Thin Δ | Reset Δ | Touch-reset Δ | Owned rate | Thinned rate | Bonus share | Thinned bonus share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| -0.000871 | -0.014216 | 0.000000 | 0.000000 | 19.073252 | 10.425883 | 0.441946 | 0.383028 |

| Reset variant | Graded changed share | Owner agreement without | Owner agreement with |
| --- | --- | --- | --- |
| candidate+reset | 0.000100 | — | — |
| candidate+touch+reset | 0.000111 | — | — |

### skillcorner_development

| Variant | Spell F1 | Macro F1 | Dead recall | Predicted spells | Reference spells |
| --- | --- | --- | --- | --- | --- |
| control | 0.606222 | 0.580751 | — | 327.200000 | 262.800000 |
| candidate | 0.603152 | 0.580185 | — | 322.600000 | 262.800000 |
| candidate+touch | 0.616479 | 0.581959 | — | 331.800000 | 262.800000 |
| candidate+touch-thin | 0.600876 | 0.574103 | — | 291.600000 | 262.800000 |
| candidate+reset | 0.603618 | 0.580149 | — | 322.000000 | 262.800000 |
| candidate+touch+reset | 0.616766 | 0.581914 | — | 331.400000 | 262.800000 |

| Touch Δ | Thin Δ | Reset Δ | Touch-reset Δ | Owned rate | Thinned rate | Bonus share | Thinned bonus share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.013327 | -0.002276 | 0.000466 | 0.000288 | 20.372259 | 10.438152 | 0.471089 | 0.403940 |

| Reset variant | Graded changed share | Owner agreement without | Owner agreement with |
| --- | --- | --- | --- |
| candidate+reset | 0.000510 | — | — |
| candidate+touch+reset | 0.000534 | — | — |

## Per-match results

### dfl-J03WN1 (stop75-jitter)

| Variant | Spell F1 | Macro F1 | Dead recall | Predicted spells | Reference spells |
| --- | --- | --- | --- | --- | --- |
| control | 0.253226 | 0.339559 | 0.000000 | 244.000000 | 500.000000 |
| candidate | 0.336408 | 0.665778 | 0.646576 | 324.000000 | 500.000000 |
| candidate+touch | 0.430909 | 0.688596 | 0.646576 | 380.000000 | 500.000000 |
| candidate+touch-thin | 0.325466 | 0.662062 | 0.646576 | 305.000000 | 500.000000 |
| candidate+reset | 0.345771 | 0.666613 | 0.646576 | 304.000000 | 500.000000 |
| candidate+touch+reset | 0.445780 | 0.689821 | 0.646576 | 365.000000 | 500.000000 |

| Touch Δ | Thin Δ | Owned rate | Thinned rate | Bonus share | Thinned bonus share |
| --- | --- | --- | --- | --- | --- |
| 0.094501 | -0.010942 | 26.581663 | 9.684478 | 0.338257 | 0.268054 |

| Reset variant | Spell F1 Δ | Graded changed share | Owner agreement without | Owner agreement with |
| --- | --- | --- | --- | --- |
| candidate+reset | 0.009363 | 0.002395 | 34/74 = 0.459459 | 40/74 = 0.540541 |
| candidate+touch+reset | 0.014871 | 0.003645 | 28/74 = 0.378378 | 35/74 = 0.472973 |

### dfl-J03WOH (stop75-jitter)

| Variant | Spell F1 | Macro F1 | Dead recall | Predicted spells | Reference spells |
| --- | --- | --- | --- | --- | --- |
| control | 0.284667 | 0.372344 | 0.000000 | 198.000000 | 402.000000 |
| candidate | 0.401159 | 0.736245 | 0.748809 | 288.000000 | 402.000000 |
| candidate+touch | 0.458311 | 0.757615 | 0.748809 | 332.000000 | 402.000000 |
| candidate+touch-thin | 0.365832 | 0.735398 | 0.748809 | 277.000000 | 402.000000 |
| candidate+reset | 0.413115 | 0.740945 | 0.748809 | 269.000000 | 402.000000 |
| candidate+touch+reset | 0.474652 | 0.758160 | 0.748809 | 316.000000 | 402.000000 |

| Touch Δ | Thin Δ | Owned rate | Thinned rate | Bonus share | Thinned bonus share |
| --- | --- | --- | --- | --- | --- |
| 0.057151 | -0.035327 | 27.025270 | 9.969225 | 0.358637 | 0.287689 |

| Reset variant | Spell F1 Δ | Graded changed share | Owner agreement without | Owner agreement with |
| --- | --- | --- | --- | --- |
| candidate+reset | 0.011955 | 0.008337 | 49/74 = 0.662162 | 59/74 = 0.797297 |
| candidate+touch+reset | 0.016341 | 0.002733 | 48/74 = 0.648649 | 55/74 = 0.743243 |

### dfl-J03WOY (stop75-jitter)

| Variant | Spell F1 | Macro F1 | Dead recall | Predicted spells | Reference spells |
| --- | --- | --- | --- | --- | --- |
| control | 0.274439 | 0.375312 | 0.000000 | 213.000000 | 456.000000 |
| candidate | 0.345067 | 0.701558 | 0.644302 | 294.000000 | 456.000000 |
| candidate+touch | 0.453894 | 0.721575 | 0.644302 | 353.000000 | 456.000000 |
| candidate+touch-thin | 0.348079 | 0.703128 | 0.644302 | 299.000000 | 456.000000 |
| candidate+reset | 0.356593 | 0.702487 | 0.644302 | 272.000000 | 456.000000 |
| candidate+touch+reset | 0.459521 | 0.721735 | 0.644302 | 337.000000 | 456.000000 |

| Touch Δ | Thin Δ | Owned rate | Thinned rate | Bonus share | Thinned bonus share |
| --- | --- | --- | --- | --- | --- |
| 0.108827 | 0.003013 | 25.795594 | 10.979192 | 0.395865 | 0.343212 |

| Reset variant | Spell F1 Δ | Graded changed share | Owner agreement without | Owner agreement with |
| --- | --- | --- | --- | --- |
| candidate+reset | 0.011527 | 0.002371 | 40/73 = 0.547945 | 44/73 = 0.602740 |
| candidate+touch+reset | 0.005627 | 0.003445 | 41/73 = 0.561644 | 41/73 = 0.561644 |

### dfl-J03WR9 (stop75-jitter)

| Variant | Spell F1 | Macro F1 | Dead recall | Predicted spells | Reference spells |
| --- | --- | --- | --- | --- | --- |
| control | 0.329453 | 0.417290 | 0.000000 | 197.000000 | 370.000000 |
| candidate | 0.391411 | 0.754885 | 0.738381 | 282.000000 | 370.000000 |
| candidate+touch | 0.486981 | 0.772930 | 0.738381 | 329.000000 | 370.000000 |
| candidate+touch-thin | 0.405573 | 0.756409 | 0.738381 | 276.000000 | 370.000000 |
| candidate+reset | 0.407512 | 0.757744 | 0.738381 | 269.000000 | 370.000000 |
| candidate+touch+reset | 0.493741 | 0.773922 | 0.738381 | 317.000000 | 370.000000 |

| Touch Δ | Thin Δ | Owned rate | Thinned rate | Bonus share | Thinned bonus share |
| --- | --- | --- | --- | --- | --- |
| 0.095570 | 0.014162 | 28.966953 | 11.145277 | 0.444493 | 0.371909 |

| Reset variant | Spell F1 Δ | Graded changed share | Owner agreement without | Owner agreement with |
| --- | --- | --- | --- | --- |
| candidate+reset | 0.016101 | 0.003092 | 28/65 = 0.430769 | 40/65 = 0.615385 |
| candidate+touch+reset | 0.006760 | 0.001648 | 26/65 = 0.400000 | 34/65 = 0.523077 |

### skillcorner-1874553 (natural)

| Variant | Spell F1 | Macro F1 | Dead recall | Predicted spells | Reference spells |
| --- | --- | --- | --- | --- | --- |
| control | 0.661565 | 0.598883 | — | 325.000000 | 250.000000 |
| candidate | 0.655888 | 0.595657 | — | 319.000000 | 250.000000 |
| candidate+touch | 0.641796 | 0.590915 | — | 329.000000 | 250.000000 |
| candidate+touch-thin | 0.658519 | 0.590382 | — | 290.000000 | 250.000000 |
| candidate+reset | 0.657042 | 0.595467 | — | 318.000000 | 250.000000 |
| candidate+touch+reset | 0.642907 | 0.590725 | — | 328.000000 | 250.000000 |

| Touch Δ | Thin Δ | Owned rate | Thinned rate | Bonus share | Thinned bonus share |
| --- | --- | --- | --- | --- | --- |
| -0.014091 | 0.002631 | 21.637317 | 10.529390 | 0.480445 | 0.410959 |

| Reset variant | Spell F1 Δ | Graded changed share | Owner agreement without | Owner agreement with |
| --- | --- | --- | --- | --- |
| candidate+reset | 0.001155 | 0.000226 | — | — |
| candidate+touch+reset | 0.001110 | 0.000226 | — | — |

### skillcorner-1886347 (natural)

| Variant | Spell F1 | Macro F1 | Dead recall | Predicted spells | Reference spells |
| --- | --- | --- | --- | --- | --- |
| control | 0.670567 | 0.589558 | — | 310.000000 | 237.000000 |
| candidate | 0.677264 | 0.592413 | — | 304.000000 | 237.000000 |
| candidate+touch | 0.623158 | 0.590582 | — | 333.000000 | 237.000000 |
| candidate+touch-thin | 0.610566 | 0.583583 | — | 293.000000 | 237.000000 |
| candidate+reset | 0.677264 | 0.592413 | — | 304.000000 | 237.000000 |
| candidate+touch+reset | 0.623158 | 0.590582 | — | 333.000000 | 237.000000 |

| Touch Δ | Thin Δ | Owned rate | Thinned rate | Bonus share | Thinned bonus share |
| --- | --- | --- | --- | --- | --- |
| -0.054106 | -0.066698 | 20.773944 | 10.656326 | 0.474547 | 0.414380 |

| Reset variant | Spell F1 Δ | Graded changed share | Owner agreement without | Owner agreement with |
| --- | --- | --- | --- | --- |
| candidate+reset | 0.000000 | 0.000000 | — | — |
| candidate+touch+reset | 0.000000 | 0.000000 | — | — |

### skillcorner-2007448 (natural)

| Variant | Spell F1 | Macro F1 | Dead recall | Predicted spells | Reference spells |
| --- | --- | --- | --- | --- | --- |
| control | 0.588650 | 0.584853 | — | 285.000000 | 226.000000 |
| candidate | 0.594444 | 0.587943 | — | 278.000000 | 226.000000 |
| candidate+touch | 0.623092 | 0.595120 | — | 285.000000 | 226.000000 |
| candidate+touch-thin | 0.615833 | 0.587285 | — | 254.000000 | 226.000000 |
| candidate+reset | 0.594444 | 0.587943 | — | 278.000000 | 226.000000 |
| candidate+touch+reset | 0.623092 | 0.595120 | — | 285.000000 | 226.000000 |

| Touch Δ | Thin Δ | Owned rate | Thinned rate | Bonus share | Thinned bonus share |
| --- | --- | --- | --- | --- | --- |
| 0.028648 | 0.021389 | 19.771621 | 10.503130 | 0.452995 | 0.390056 |

| Reset variant | Spell F1 Δ | Graded changed share | Owner agreement without | Owner agreement with |
| --- | --- | --- | --- | --- |
| candidate+reset | 0.000000 | 0.000193 | — | — |
| candidate+touch+reset | 0.000000 | 0.000124 | — | — |

### skillcorner-2007721 (natural)

| Variant | Spell F1 | Macro F1 | Dead recall | Predicted spells | Reference spells |
| --- | --- | --- | --- | --- | --- |
| control | 0.604930 | 0.591023 | — | 320.000000 | 248.000000 |
| candidate | 0.595398 | 0.587314 | — | 317.000000 | 248.000000 |
| candidate+touch | 0.613238 | 0.593486 | — | 311.000000 | 248.000000 |
| candidate+touch-thin | 0.616154 | 0.585183 | — | 272.000000 | 248.000000 |
| candidate+reset | 0.595398 | 0.587314 | — | 317.000000 | 248.000000 |
| candidate+touch+reset | 0.613238 | 0.593486 | — | 311.000000 | 248.000000 |

| Touch Δ | Thin Δ | Owned rate | Thinned rate | Bonus share | Thinned bonus share |
| --- | --- | --- | --- | --- | --- |
| 0.017840 | 0.020756 | 20.277493 | 10.300707 | 0.514014 | 0.436311 |

| Reset variant | Spell F1 Δ | Graded changed share | Owner agreement without | Owner agreement with |
| --- | --- | --- | --- | --- |
| candidate+reset | 0.000000 | 0.000000 | — | — |
| candidate+touch+reset | 0.000000 | 0.000000 | — | — |

### skillcorner-2010085 (natural)

| Variant | Spell F1 | Macro F1 | Dead recall | Predicted spells | Reference spells |
| --- | --- | --- | --- | --- | --- |
| control | 0.588994 | 0.586511 | — | 295.000000 | 232.000000 |
| candidate | 0.578967 | 0.583850 | — | 291.000000 | 232.000000 |
| candidate+touch | 0.609266 | 0.585327 | — | 286.000000 | 232.000000 |
| candidate+touch-thin | 0.575254 | 0.582525 | — | 261.000000 | 232.000000 |
| candidate+reset | 0.578967 | 0.583850 | — | 291.000000 | 232.000000 |
| candidate+touch+reset | 0.609266 | 0.585327 | — | 286.000000 | 232.000000 |

| Touch Δ | Thin Δ | Owned rate | Thinned rate | Bonus share | Thinned bonus share |
| --- | --- | --- | --- | --- | --- |
| 0.030299 | -0.003714 | 19.955689 | 10.571293 | 0.484545 | 0.420576 |

| Reset variant | Spell F1 Δ | Graded changed share | Owner agreement without | Owner agreement with |
| --- | --- | --- | --- | --- |
| candidate+reset | 0.000000 | 0.000265 | — | — |
| candidate+touch+reset | 0.000000 | 0.000502 | — | — |

### skillcorner-2011166 (natural)

| Variant | Spell F1 | Macro F1 | Dead recall | Predicted spells | Reference spells |
| --- | --- | --- | --- | --- | --- |
| control | 0.538854 | 0.556213 | — | 357.000000 | 271.000000 |
| candidate | 0.534400 | 0.557234 | — | 354.000000 | 271.000000 |
| candidate+touch | 0.545904 | 0.557704 | — | 376.000000 | 271.000000 |
| candidate+touch-thin | 0.511288 | 0.539921 | — | 358.000000 | 271.000000 |
| candidate+reset | 0.534400 | 0.557234 | — | 354.000000 | 271.000000 |
| candidate+touch+reset | 0.545904 | 0.557704 | — | 376.000000 | 271.000000 |

| Touch Δ | Thin Δ | Owned rate | Thinned rate | Bonus share | Thinned bonus share |
| --- | --- | --- | --- | --- | --- |
| 0.011504 | -0.023112 | 18.007388 | 10.273446 | 0.388819 | 0.334289 |

| Reset variant | Spell F1 Δ | Graded changed share | Owner agreement without | Owner agreement with |
| --- | --- | --- | --- | --- |
| candidate+reset | 0.000000 | 0.000000 | — | — |
| candidate+touch+reset | 0.000000 | 0.000000 | — | — |

### skillcorner-2013725 (natural)

| Variant | Spell F1 | Macro F1 | Dead recall | Predicted spells | Reference spells |
| --- | --- | --- | --- | --- | --- |
| control | 0.599106 | 0.564915 | — | 365.000000 | 306.000000 |
| candidate | 0.596702 | 0.564031 | — | 361.000000 | 306.000000 |
| candidate+touch | 0.586938 | 0.562498 | — | 383.000000 | 306.000000 |
| candidate+touch-thin | 0.592000 | 0.551402 | — | 319.000000 | 306.000000 |
| candidate+reset | 0.596702 | 0.564031 | — | 361.000000 | 306.000000 |
| candidate+touch+reset | 0.586938 | 0.562498 | — | 383.000000 | 306.000000 |

| Touch Δ | Thin Δ | Owned rate | Thinned rate | Bonus share | Thinned bonus share |
| --- | --- | --- | --- | --- | --- |
| -0.009764 | -0.004702 | 20.173528 | 10.239081 | 0.474099 | 0.409470 |

| Reset variant | Spell F1 Δ | Graded changed share | Owner agreement without | Owner agreement with |
| --- | --- | --- | --- | --- |
| candidate+reset | 0.000000 | 0.000000 | — | — |
| candidate+touch+reset | 0.000000 | 0.000000 | — | — |

### skillcorner-2015213 (natural)

| Variant | Spell F1 | Macro F1 | Dead recall | Predicted spells | Reference spells |
| --- | --- | --- | --- | --- | --- |
| control | 0.581395 | 0.564471 | — | 392.000000 | 296.000000 |
| candidate | 0.578235 | 0.562257 | — | 384.000000 | 296.000000 |
| candidate+touch | 0.609437 | 0.566118 | — | 361.000000 | 296.000000 |
| candidate+touch-thin | 0.579935 | 0.554302 | — | 322.000000 | 296.000000 |
| candidate+reset | 0.578235 | 0.562257 | — | 384.000000 | 296.000000 |
| candidate+touch+reset | 0.609437 | 0.566118 | — | 361.000000 | 296.000000 |

| Touch Δ | Thin Δ | Owned rate | Thinned rate | Bonus share | Thinned bonus share |
| --- | --- | --- | --- | --- | --- |
| 0.031202 | 0.001700 | 18.134090 | 10.357640 | 0.432704 | 0.381594 |

| Reset variant | Spell F1 Δ | Graded changed share | Owner agreement without | Owner agreement with |
| --- | --- | --- | --- | --- |
| candidate+reset | 0.000000 | 0.000287 | — | — |
| candidate+touch+reset | 0.000000 | 0.000341 | — | — |

### skillcorner-2016236 (natural)

| Variant | Spell F1 | Macro F1 | Dead recall | Predicted spells | Reference spells |
| --- | --- | --- | --- | --- | --- |
| control | 0.592793 | 0.568595 | — | 366.000000 | 300.000000 |
| candidate | 0.589759 | 0.569442 | — | 364.000000 | 300.000000 |
| candidate+touch | 0.621302 | 0.575937 | — | 376.000000 | 300.000000 |
| candidate+touch-thin | 0.562776 | 0.558923 | — | 334.000000 | 300.000000 |
| candidate+reset | 0.590937 | 0.569451 | — | 362.000000 | 300.000000 |
| candidate+touch+reset | 0.621630 | 0.575898 | — | 375.000000 | 300.000000 |

| Touch Δ | Thin Δ | Owned rate | Thinned rate | Bonus share | Thinned bonus share |
| --- | --- | --- | --- | --- | --- |
| 0.031543 | -0.026983 | 20.323138 | 10.347864 | 0.463359 | 0.388639 |

| Reset variant | Spell F1 Δ | Graded changed share | Owner agreement without | Owner agreement with |
| --- | --- | --- | --- | --- |
| candidate+reset | 0.001178 | 0.001865 | — | — |
| candidate+touch+reset | 0.000328 | 0.001819 | — | — |

### skillcorner-2017461 (natural)

| Variant | Spell F1 | Macro F1 | Dead recall | Predicted spells | Reference spells |
| --- | --- | --- | --- | --- | --- |
| control | 0.538813 | 0.553510 | — | 374.000000 | 283.000000 |
| candidate | 0.536406 | 0.551465 | — | 368.000000 | 283.000000 |
| candidate+touch | 0.525610 | 0.540655 | — | 373.000000 | 283.000000 |
| candidate+touch-thin | 0.532683 | 0.544684 | — | 332.000000 | 283.000000 |
| candidate+reset | 0.536406 | 0.551465 | — | 368.000000 | 283.000000 |
| candidate+touch+reset | 0.525610 | 0.540655 | — | 373.000000 | 283.000000 |

| Touch Δ | Thin Δ | Owned rate | Thinned rate | Bonus share | Thinned bonus share |
| --- | --- | --- | --- | --- | --- |
| -0.010796 | -0.003723 | 18.173346 | 10.541296 | 0.399648 | 0.348564 |

| Reset variant | Spell F1 Δ | Graded changed share | Owner agreement without | Owner agreement with |
| --- | --- | --- | --- | --- |
| candidate+reset | 0.000000 | 0.000212 | — | — |
| candidate+touch+reset | 0.000000 | 0.000212 | — | — |

### wcsf-used-match (stop75-jitter)

| Variant | Spell F1 | Macro F1 | Dead recall | Predicted spells | Reference spells |
| --- | --- | --- | --- | --- | --- |
| control | 0.396226 | 0.380577 | 0.000000 | 331.000000 | 411.000000 |
| candidate | 0.438631 | 0.699606 | 0.640624 | 407.000000 | 411.000000 |
| candidate+touch | 0.496357 | 0.714654 | 0.640624 | 440.000000 | 411.000000 |
| candidate+touch-thin | 0.431083 | 0.700285 | 0.640624 | 374.000000 | 411.000000 |
| candidate+reset | 0.460177 | 0.700951 | 0.640624 | 380.000000 | 411.000000 |
| candidate+touch+reset | 0.511594 | 0.715792 | 0.640624 | 417.000000 | 411.000000 |

| Touch Δ | Thin Δ | Owned rate | Thinned rate | Bonus share | Thinned bonus share |
| --- | --- | --- | --- | --- | --- |
| 0.057726 | -0.007548 | 30.280489 | 10.432164 | 0.401608 | 0.336029 |

| Reset variant | Spell F1 Δ | Graded changed share | Owner agreement without | Owner agreement with |
| --- | --- | --- | --- | --- |
| candidate+reset | 0.021546 | 0.003054 | 33/74 = 0.445946 | 44/74 = 0.594595 |
| candidate+touch+reset | 0.015237 | 0.002050 | 30/74 = 0.405405 | 41/74 = 0.554054 |

## Fixed decisions

| Gate | Value | Minimum | Pass |
| --- | --- | --- | --- |
| A | -0.000871 | -0.010000 | True |
| B | -0.014216 | -0.010000 | False |
| C | -0.002969 | 0.020000 | False |
| D | 0.000000 | -0.020000 | True |
| E | 0.018823 | 0.005000 | True |
| F | 0.000000 | -0.005000 | True |
| G | 0.000000 | -0.020000 | True |

Gate E per-match gains: {'dfl-J03WR9': 0.016100694144416616, 'wcsf-used-match': 0.02154618430447669}; neither negative: True.

Recommended existing file: **candidate**; SHA-256 `31b947d3b250b6267a7d8f0aac0c4e4eafd82a4fc873c82759806e676b1bf963`. Decoder restart qualifies: **True**. No restart release was built. The user makes the final choice.

## Comparison with the earlier nongating probe

The brief gives rounded values for three nongating DFL matches in list order WN1, WOH, WOY. The table compares that mapping; no underlying probe receipt was supplied. All comparisons use the plain candidate reset path.

| Match | Prior approximate gain | This gain | Prior agreement without/with | This agreement without/with |
| --- | --- | --- | --- | --- |
| dfl-J03WN1 | 0.009000 | 0.009363 | .46 / .54 | 0.459459 / 0.540541 |
| dfl-J03WOH | 0.012000 | 0.011955 | .66 / .80 | 0.662162 / 0.797297 |
| dfl-J03WOY | 0.012000 | 0.011527 | .55 / .60 | 0.547945 / 0.602740 |

Development SkillCorner plain-reset gain range: +0.000000 to +0.001178; prior rounded range 0 to +.001.

Owner agreement uses the fixed definition in the protocol; different eligibility or restart indexing may produce different figures. These diagnostics do not gate selection.

## Limits

- Every match has been scored before; touch settings were selected on five development SkillCorner matches and dfl-J03WN1.
- This is the third test of touch evidence and is post-hoc.
- SkillCorner references have no dead ball and longer possessions than the challenge.
- White noise and random thinning match two tracking statistics, not the causes of missing touches; real misses may be nonrandom.
- Touch gating sets contain five and three matches.
- Expected reset gain is about 0.01, below what two matches can confirm; gate E is a consistency check, not proof.
- The reset idea was chosen after a probe on nongating matches.
- The regime hides the ball up to two seconds after a restart, which may not match the provided track reacquisition delay.

## Verification and preservation

Synthetic tests were written first and observed failing before implementation. The initial full suite failed in the default temporary directory with Windows permission errors. After moving TEMP/TMP to the writable checkout .tmp directory, the full run executed 770 cases with one failure, four errors and 22 skips: four link/junction checks were permission-blocked and the official-code contract class had the wrong folder path. All six affected methods pass with the corrected nested official-code path and permitted temporary-link operations. The latest 16 experiment tests pass. Across these runs, 773 current cases are accounted for: 751 passed, 22 skipped; this is not a single green 773-case run. See verification.json for the exact counts and environment corrections. No scientific run was repeated. The code review was performed by a separate agent in the same model family.

Sequencing deviation: the profile overlapped the first full suite, and scientific scoring began after all 16 experiment tests and profile gates passed while the corrected legacy suite was still running. No setting, variant or gate changed after any real score was observed.

Both existing Desktop submission hashes are checked after the run. No public ground truth was opened, no submission was generated, and nothing was pushed, merged or uploaded.
