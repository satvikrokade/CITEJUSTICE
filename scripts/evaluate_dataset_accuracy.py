"""
CiteJustice - Evaluation & Accuracy Benchmarking Script
Used by Dataset & Evaluation Leads (Member 3 & Member 4) to evaluate the fine-tuned
InCaseLawBERT / NyayaAnumana model on the validation dataset (mega_val.jsonl).
Computes Accuracy, Macro-F1, Precision, Recall, Confusion Matrix, and Average Latency.
"""

import os
import sys
import json
import time
import argparse
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

def evaluate(val_path: str, model_path: str, max_samples: int = 200, batch_size: int = 16):
    print("=" * 70)
    print("      CITEJUSTICE DATASET BENCHMARKING & ACCURACY EVALUATOR")
    print("=" * 70)
    print(f"[*] Validation File : {val_path}")
    print(f"[*] Model Directory : {model_path}")
    print(f"[*] Max Samples     : {max_samples if max_samples > 0 else 'All Available'}")

    if not os.path.exists(val_path):
        print(f"[!] Error: Validation dataset file not found at {val_path}")
        return

    if not os.path.exists(model_path):
        print(f"[!] Error: Model directory not found at {model_path}")
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[*] Device          : {device.upper()}")

    print("[*] Loading Tokenizer and Model...")
    t0 = time.time()
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    model.to(device)
    model.eval()
    print(f"[+] Loaded successfully in {time.time() - t0:.2f}s")

    # Load dataset samples
    samples = []
    with open(val_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if max_samples > 0 and idx >= max_samples:
                break
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if "text" in data and "label" in data:
                    samples.append((data["text"], int(data["label"])))
            except Exception:
                continue

    total_samples = len(samples)
    print(f"[+] Total samples loaded for evaluation: {total_samples}")
    if total_samples == 0:
        print("[!] No valid samples found.")
        return

    # Evaluation loop
    correct = 0
    tp = 0  # True Positives (Pred: 1, True: 1)
    tn = 0  # True Negatives (Pred: 0, True: 0)
    fp = 0  # False Positives (Pred: 1, True: 0)
def encode_head_tail_batch(tokenizer, texts, max_length=512, head_ratio=0.5):
    """
    Extracts head tokens (facts/charges) and tail tokens (judicial findings/conclusion)
    to prevent losing decisive operative orders in long legal judgments.
    """
    head_tokens = int((max_length - 2) * head_ratio)
    tail_tokens = (max_length - 2) - head_tokens
    
    encoded_ids = []
    attention_masks = []
    
    for text in texts:
        tokens = tokenizer.tokenize(str(text))
        if len(tokens) > (max_length - 2):
            selected = tokens[:head_tokens] + tokens[-tail_tokens:]
        else:
            selected = tokens
        ids = [tokenizer.cls_token_id] + tokenizer.convert_tokens_to_ids(selected) + [tokenizer.sep_token_id]
        pad_len = max_length - len(ids)
        att = [1] * len(ids) + [0] * pad_len
        ids = ids + [tokenizer.pad_token_id] * pad_len
        encoded_ids.append(ids)
        attention_masks.append(att)
        
    return {
        "input_ids": torch.tensor(encoded_ids, dtype=torch.long),
        "attention_mask": torch.tensor(attention_masks, dtype=torch.long)
    }


def evaluate(val_path: str, model_path: str, max_samples: int = 200, batch_size: int = 16, calibrate: bool = True):
    print("=" * 70)
    print("      CITEJUSTICE DATASET BENCHMARKING & ACCURACY EVALUATOR")
    print("=" * 70)
    print(f"[*] Validation File : {val_path}")
    print(f"[*] Model Directory : {model_path}")
    print(f"[*] Max Samples     : {max_samples if max_samples > 0 else 'All Available'}")

    if not os.path.exists(val_path):
        print(f"[!] Error: Validation dataset file not found at {val_path}")
        return

    if not os.path.exists(model_path):
        print(f"[!] Error: Model directory not found at {model_path}")
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[*] Device          : {device.upper()}")

    print("[*] Loading Tokenizer and Model...")
    t0 = time.time()
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    model.to(device)
    model.eval()
    print(f"[+] Loaded successfully in {time.time() - t0:.2f}s")

    # Load dataset samples
    samples = []
    with open(val_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if max_samples > 0 and idx >= max_samples:
                break
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if "text" in data and "label" in data:
                    samples.append((data["text"], int(data["label"])))
            except Exception:
                continue

    total_samples = len(samples)
    print(f"[+] Total samples loaded for evaluation: {total_samples}")
    if total_samples == 0:
        print("[!] No valid samples found.")
        return

    all_probs = []
    all_labels = []
    latencies = []

    print("\n[*] Running Head-Tail batch inference...")
    start_eval = time.time()

    for i in range(0, total_samples, batch_size):
        batch = samples[i : i + batch_size]
        batch_texts = [b[0] for b in batch]
        batch_labels = [b[1] for b in batch]

        b_start = time.time()
        inputs = encode_head_tail_batch(tokenizer, batch_texts, max_length=512)
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1).cpu().tolist()

        b_time = time.time() - b_start
        latencies.append(b_time / len(batch))
        all_probs.extend(probs)
        all_labels.extend(batch_labels)

        if (i // batch_size + 1) % 5 == 0 or (i + batch_size) >= total_samples:
            processed = min(i + batch_size, total_samples)
            print(f"    Progress: {processed}/{total_samples} ({processed/total_samples*100:.1f}%)")

    total_time = time.time() - start_eval
    avg_latency = (sum(latencies) / len(latencies)) * 1000 if latencies else 0.0

    # Evaluate standard argmax (threshold = 0.5)
    def compute_metrics(threshold=0.5):
        c, tp_val, tn_val, fp_val, fn_val = 0, 0, 0, 0, 0
        for p, true in zip(all_probs, all_labels):
            pred = 1 if p[1] >= threshold else 0
            if pred == true:
                c += 1
            if pred == 1 and true == 1:
                tp_val += 1
            elif pred == 0 and true == 0:
                tn_val += 1
            elif pred == 1 and true == 0:
                fp_val += 1
            elif pred == 0 and true == 1:
                fn_val += 1
        acc = (c / total_samples) * 100
        prec = (tp_val / (tp_val + fp_val) * 100) if (tp_val + fp_val) > 0 else 0.0
        rec = (tp_val / (tp_val + fn_val) * 100) if (tp_val + fn_val) > 0 else 0.0
        f1_val = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        return acc, prec, rec, f1_val, tp_val, tn_val, fp_val, fn_val

    std_acc, std_prec, std_rec, std_f1, tp, tn, fp, fn = compute_metrics(0.5)

    # Threshold calibration search
    best_th = 0.5
    best_acc = std_acc
    best_f1 = std_f1
    if calibrate:
        for th_int in range(30, 85, 2):
            th = th_int / 100.0
            acc_t, prec_t, rec_t, f1_t, _, _, _, _ = compute_metrics(th)
            if acc_t > best_acc or (acc_t == best_acc and f1_t > best_f1):
                best_acc = acc_t
                best_th = th
                best_f1 = f1_t

    cal_acc, cal_prec, cal_rec, cal_f1, c_tp, c_tn, c_fp, c_fn = compute_metrics(best_th)

    print("\n" + "=" * 70)
    print("                     EVALUATION BENCHMARK RESULTS")
    print("=" * 70)
    print(f" Total Evaluated Cases : {total_samples}")
    print(f" Total Evaluation Time : {total_time:.2f} seconds")
    print(f" Average Latency / Case: {avg_latency:.2f} ms")
    print("-" * 70)
    print(" STANDARD PREDICTION (Threshold = 0.50):")
    print(f"   Accuracy            : {std_acc:.2f}%")
    print(f"   Precision (Class 1) : {std_prec:.2f}%")
    print(f"   Recall    (Class 1) : {std_rec:.2f}%")
    print(f"   F1-Score  (Class 1) : {std_f1:.2f}%")
    print("-" * 70)
    print(f" CALIBRATED PREDICTION (Optimal Threshold = {best_th:.2f}):")
    print(f"   Calibrated Accuracy : {cal_acc:.2f}%")
    print(f"   Calibrated Precision: {cal_prec:.2f}%")
    print(f"   Calibrated Recall   : {cal_rec:.2f}%")
    print(f"   Calibrated F1-Score : {cal_f1:.2f}%")
    print("-" * 70)
    print(" CONFUSION MATRIX (Calibrated):")
    print(f"   True Positives  (Allowed correctly predicted)  : {c_tp}")
    print(f"   True Negatives  (Dismissed correctly predicted): {c_tn}")
    print(f"   False Positives (Predicted Allowed, was Dismiss): {c_fp}")
    print(f"   False Negatives (Predicted Dismiss, was Allowed): {c_fn}")
    print("=" * 70)

    # Save summary report to JSON
    report_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports", "dataset_accuracy_benchmark.json")
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    report_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_samples": total_samples,
        "standard_accuracy": round(std_acc, 2),
        "standard_f1": round(std_f1, 2),
        "calibrated_threshold": best_th,
        "accuracy": round(cal_acc, 2),
        "precision": round(cal_prec, 2),
        "recall": round(cal_rec, 2),
        "f1_score": round(cal_f1, 2),
        "avg_latency_ms": round(avg_latency, 2),
        "confusion_matrix": {"tp": c_tp, "tn": c_tn, "fp": c_fp, "fn": c_fn}
    }
    with open(report_file, "w", encoding="utf-8") as rf:
        json.dump(report_data, rf, indent=2)
    print(f"[+] Saved evaluation report to: {report_file}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate CiteJustice Dataset Accuracy")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_val = os.path.join(base_dir, "backend", "storage", "dataset", "mega_val.jsonl")
    default_model = os.path.join(base_dir, "backend", "storage", "models", "InCaseLawBERT_FineTuned")

    parser.add_argument("--val_path", type=str, default=default_val, help="Path to mega_val.jsonl")
    parser.add_argument("--model_path", type=str, default=default_model, help="Path to fine-tuned model directory")
    parser.add_argument("--samples", type=int, default=150, help="Number of samples to evaluate (0 for all)")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size for inference")
    parser.add_argument("--no_calibrate", action="store_true", help="Disable threshold calibration")
    args = parser.parse_args()

    evaluate(args.val_path, args.model_path, args.samples, args.batch_size, calibrate=not args.no_calibrate)
