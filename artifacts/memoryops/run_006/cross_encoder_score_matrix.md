# Cross-Encoder Score Matrix (FM-15)

RAW_SCORE = Graphiti `BGERerankerClient.rank` / `CrossEncoder.predict` (official; activation_fn=Sigmoid).
NORMALIZED_SCORE = null (no additional lab-side normalization).
LOGIT_SCORE = Identity activation (transparency only).

## RAW_SCORE grid

| Query | F1 | F2 | F3 | F4 |
|---|---:|---:|---:|---:|
| Q1 | 0.974169 | 0.030276 | 0.007323 | 0.000021 |
| Q2 | 0.002514 | 0.997204 | 0.000018 | 0.013468 |
| Q3 | 0.000020 | 0.000021 | 0.049960 | 0.032244 |
| Q4 | 0.007880 | 0.000030 | 0.005133 | 0.000019 |
| Q5 | 0.023136 | 0.005334 | 0.000016 | 0.000127 |

## Per-pair detail

| Q | Fact | Gold | Rank | RAW_SCORE | LOGIT_SCORE | Fact text |
|---|---|---|---:|---:|---:|---|
| Q1 | F1 | True | 1 | 0.974169 | 3.630003 | Alice works on Project Orion. |
| Q1 | F2 | False | 2 | 0.030276 | -3.466648 | Project Orion uses Python. |
| Q1 | F3 | False | 3 | 0.007323 | -4.909389 | Bob works on Project Nova. |
| Q1 | F4 | False | 4 | 0.000021 | -10.791616 | Project Nova uses Rust. |
| Q2 | F1 | False | 3 | 0.002514 | -5.983431 | Alice works on Project Orion. |
| Q2 | F2 | True | 1 | 0.997204 | 5.876667 | Project Orion uses Python. |
| Q2 | F3 | False | 4 | 0.000018 | -10.928853 | Bob works on Project Nova. |
| Q2 | F4 | False | 2 | 0.013468 | -4.293907 | Project Nova uses Rust. |
| Q3 | F1 | False | 4 | 0.000020 | -10.804523 | Alice works on Project Orion. |
| Q3 | F2 | False | 3 | 0.000021 | -10.782548 | Project Orion uses Python. |
| Q3 | F3 | True | 1 | 0.049960 | -2.945272 | Bob works on Project Nova. |
| Q3 | F4 | True | 2 | 0.032244 | -3.401649 | Project Nova uses Rust. |
| Q4 | F1 | False | 1 | 0.007880 | -4.835470 | Alice works on Project Orion. |
| Q4 | F2 | False | 3 | 0.000030 | -10.428930 | Project Orion uses Python. |
| Q4 | F3 | False | 2 | 0.005133 | -5.266829 | Bob works on Project Nova. |
| Q4 | F4 | False | 4 | 0.000019 | -10.888789 | Project Nova uses Rust. |
| Q5 | F1 | False | 1 | 0.023136 | -3.742950 | Alice works on Project Orion. |
| Q5 | F2 | False | 2 | 0.005334 | -5.228238 | Project Orion uses Python. |
| Q5 | F3 | False | 4 | 0.000016 | -11.013418 | Bob works on Project Nova. |
| Q5 | F4 | False | 3 | 0.000127 | -8.974737 | Project Nova uses Rust. |

