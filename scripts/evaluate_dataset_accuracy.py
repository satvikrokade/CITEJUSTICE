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
    fn = 0  # False Negatives (Pred: 0, True: 1)

    latencies = []
    print("\n[*] Running inference across batches...")
    start_eval = time.time()

    for i in range(0, total_samples, batch_size):
        batch = samples[i : i + batch_size]
        batch_texts = [b[0][:1500] for b in batch]  # Truncate context to 1500 chars for efficiency
        batch_labels = [b[1] for b in batch]

        b_start = time.time()
        inputs = tokenizer(batch_texts, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model(**inputs)
            preds = torch.argmax(outputs.logits, dim=1).cpu().tolist()
        b_time = time.time() - b_start
        latencies.append(b_time / len(batch))

        for pred, true in zip(preds, batch_labels):
            if pred == true:
                correct += 1
            if pred == 1 and true == 1:
                tp += 1
            elif pred == 0 and true == 0:
                tn += 1
            elif pred == 1 and true == 0:
                fp += 1
            elif pred == 0 and true == 1:
                fn += 1

        if (i // batch_size + 1) % 5 == 0 or (i + batch_size) >= total_samples:
            processed = min(i + batch_size, total_samples)
            print(f"    Progress: {processed}/{total_samples} ({processed/total_samples*100:.1f}%)")

    total_time = time.time() - start_eval
    accuracy = (correct / total_samples) * 100
    precision = (tp / (tp + fp) * 100) if (tp + fp) > 0 else 0.0
    recall = (tp / (tp + fn) * 100) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    avg_latency = (sum(latencies) / len(latencies)) * 1000 if latencies else 0.0

    print("\n" + "=" * 70)
    print("                     EVALUATION BENCHMARK RESULTS")
    print("=" * 70)
    print(f" Total Evaluated Cases : {total_samples}")
    print(f" Total Evaluation Time : {total_time:.2f} seconds")
    print(f" Average Latency / Case: {avg_latency:.2f} ms")
    print("-" * 70)
    print(f" Accuracy              : {accuracy:.2f}%")
    print(f" Precision (Class 1)   : {precision:.2f}%")
    print(f" Recall    (Class 1)   : {recall:.2f}%")
    print(f" F1-Score  (Class 1)   : {f1:.2f}%")
    print("-" * 70)
    print(" CONFUSION MATRIX:")
    print(f"   True Positives  (Allowed correctly predicted)  : {tp}")
    print(f"   True Negatives  (Dismissed correctly predicted): {tn}")
    print(f"   False Positives (Predicted Allowed, was Dismiss): {fp}")
    print(f"   False Negatives (Predicted Dismiss, was Allowed): {fn}")
    print("=" * 70)

    # Save summary report to JSON
    report_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports", "dataset_accuracy_benchmark.json")
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    report_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_samples": total_samples,
        "accuracy": round(accuracy, 2),
        "precision": round(precision, 2),
        "recall": round(recall, 2),
        "f1_score": round(f1, 2),
        "avg_latency_ms": round(avg_latency, 2),
        "confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn}
    }
    with open(report_file, "w", encoding="utf-8") as rf:
        json.dump(report_data, rf, indent=2)
    print(f"[+] Saved evaluation report to: {report_file}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate CiteJustice Dataset Accuracy")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_val = os.path.join(base_dir, "backend", "storage", "dataset", "mega_val.jsonl")
    default_model = os.path.join(base_dir, "backend", "storage", "models", "InCaseLawBERT")

    parser.add_argument("--val_path", type=str, default=default_val, help="Path to mega_val.jsonl")
    parser.add_argument("--model_path", type=str, default=default_model, help="Path to model directory")
    parser.add_argument("--samples", type=int, default=100, help="Number of samples to evaluate (0 for all)")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size for inference")
    args = parser.parse_args()

    evaluate(args.val_path, args.model_path, args.samples, args.batch_size)
