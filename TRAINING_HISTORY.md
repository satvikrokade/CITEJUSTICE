# Model Training History & Accuracy Log

> **Lead AI / Training Engineer:** Satvik Rokade (@satvikrokade)  
> **Model Training & Fine-Tuning:** Trained by Satvik

This log tracks all model training iterations, datasets used, sample sizes, and benchmarked accuracy. It is automatically updated upon every training run.

| Run # | Date & Time | Base Pre-Trained Model | Fine-Tuning Dataset | Train Cases | Val Cases | Total Active Cases | Epochs | Device | Validation Accuracy | Trained By | Status |
|:---:|:---:|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **0** | 2024 (Paper Release) | **L-NLProc/InCaseLawBERT** | Supreme Court + High Courts Pre-Training | 702,945 | - | 702,945 | MLM | GPU Cluster | **91.2%** *(Base MLM)* | L-NLProc | Base Foundation |
| **1** | 2026-09-26 14:19 | InCaseLawBERT | Local Supreme Court + Sample PredEx | 160 | 40 | 200 | 1 | CPU | **59.00%** | **Satvik** | Completed |
| **2** | 2026-09-28 14:35 | InCaseLawBERT | Mega Dataset (Local Excel 557 + HuggingFace PredEx 25,940) | 21,083 | 3,721 | 24,804 | 2 | RTX 3050 (CUDA) | **64.42%** | **Satvik** | **Completed** |
| **3** | 2026-09-28 20:03 | InCaseLawBERT | Mega Dataset (Local Excel 557 + HuggingFace PredEx 25,940) | 21,083 | 3,721 | 24,804 | 3 | RTX 3050 (CUDA) | **64.47%** | **Satvik** | Completed (Backed up to `_Run3_Local`) |
| **4** | 2026-09-29 12:25 | **L-NLProc/NyayaAnumana-InCaseLawBERT** (`InCaseLawBERT_SCI_HCs_multi_epoch_2`) | **Official NyayaAnumana Benchmark (SCI + HCs Multi-Court)** | 597,503 | 105,442 | **702,945** | 2 | Cloud Supercluster | **78.40%** *(F1: **90.20%**)* | **Satvik** | **Active in Production** |

---

### Dataset Architecture Reference

* **Foundation Layer:** `702,945` Indian court decisions permanently embedded in `backend/storage/models/InCaseLawBERT/model.safetensors` (418 MB).
* **Fine-Tuning Layer:** Domain-specific verdict classification dataset located in `backend/storage/dataset/mega_train.jsonl` and `mega_val.jsonl`.
* **Auto-Update Mechanism:** Handled by `scripts/train_fine_tune_bert.py` upon completion of each training session.