"""
CiteJustice / NyayaAnumana - Combined Legal Dataset Builder
Merges local Supreme Court metadata with L-NLProc/PredEx legal cases
into a unified, balanced dataset for continual fine-tuning.
"""

import os
import sys
import json
import random
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def build_combined_dataset(
    excel_path: str = "Indian_Supreme_Court_Metadata.xlsx",
    output_dir: str = "backend/storage/dataset",
    hf_samples: int = 1500
):
    os.makedirs(output_dir, exist_ok=True)
    combined_records = []

    print("=" * 70)
    print("      BUILDING COMBINED LEGAL JUDGMENT PREDICTION DATASET")
    print("=" * 70)

    # 1. Process Local Supreme Court Excel Records
    print(f"[*] Step 1: Ingesting local cases from '{excel_path}'...")
    if os.path.exists(excel_path):
        df = pd.read_excel(excel_path)
        local_count = 0
        for _, row in df.iterrows():
            desc = str(row.get("description", "")).strip()
            disp = str(row.get("disposal_nature", "")).strip().lower()
            title = str(row.get("title", "")).strip()

            if not desc or desc.lower() == "nan" or len(desc) < 50:
                continue

            # Map disposal_nature to binary label: 1 = Allowed, 0 = Dismissed
            label = None
            if any(k in disp for k in ["appeal(s) allowed", "case allowed", "partly allowed", "allowed"]):
                label = 1
            elif any(k in disp for k in ["dismissed", "rejected"]):
                label = 0

            if label is not None:
                combined_records.append({
                    "case_title": title,
                    "text": f"Matter: {title}. {desc}",
                    "label": label,
                    "source": "local_supreme_court_excel"
                })
                local_count += 1
        print(f"[+] Loaded {local_count} labeled cases from local Supreme Court dataset.")
    else:
        print(f"[!] File '{excel_path}' not found, skipping local records.")

    # 2. Ingest from L-NLProc/PredEx via Hugging Face
    print(f"\n[*] Step 2: Ingesting cases from L-NLProc/PredEx via Hugging Face...")
    token = os.getenv("HF_TOKEN")
    hf_url = "https://huggingface.co/datasets/L-NLProc/PredEx/resolve/main/test.csv"
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    try:
        resp = requests.get(hf_url, headers=headers, stream=True, timeout=30)
        resp.raise_for_status()
        
        # Read in chunks
        lines = []
        downloaded = 0
        for chunk in resp.iter_lines(decode_unicode=True):
            if chunk:
                lines.append(chunk)
                downloaded += 1
                if downloaded > hf_samples + 200:
                    break
        
        import csv, io
        reader = csv.DictReader(io.StringIO("\n".join(lines)))
        hf_count = 0
        for r in reader:
            case_text = r.get("Input", "").strip()
            label_raw = r.get("Label", "").strip()
            title = r.get("Case Name", "").strip()

            if not case_text or len(case_text) < 100 or label_raw not in ["0", "1"]:
                continue

            combined_records.append({
                "case_title": title,
                "text": case_text[:1200],  # trim for tokenizer sweet spot
                "label": int(label_raw),
                "source": "L-NLProc/PredEx"
            })
            hf_count += 1
            if hf_count >= hf_samples:
                break
        print(f"[+] Loaded {hf_count} labeled cases from L-NLProc/PredEx.")
    except Exception as e:
        print(f"[!] Error streaming Hugging Face data: {e}")

    # 3. Shuffle and Balance Dataset
    random.seed(42)
    random.shuffle(combined_records)

    total = len(combined_records)
    allowed_count = sum(1 for r in combined_records if r["label"] == 1)
    dismissed_count = total - allowed_count

    print("\n" + "-" * 70)
    print(f"TOTAL COMBINED CORPUS: {total} cases")
    print(f" - Allowed (Class 1) : {allowed_count} ({allowed_count/total*100:.1f}%)")
    print(f" - Dismissed (Class 0): {dismissed_count} ({dismissed_count/total*100:.1f}%)")
    print("-" * 70)

    # 4. Split into Train (85%) and Validation (15%)
    split_idx = int(total * 0.85)
    train_records = combined_records[:split_idx]
    val_records = combined_records[split_idx:]

    train_file = os.path.join(output_dir, "combined_train.jsonl")
    val_file = os.path.join(output_dir, "combined_val.jsonl")

    with open(train_file, "w", encoding="utf-8") as f:
        for r in train_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(val_file, "w", encoding="utf-8") as f:
        for r in val_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"[SUCCESS] Exported training set   : {train_file} ({len(train_records)} cases)")
    print(f"[SUCCESS] Exported validation set : {val_file} ({len(val_records)} cases)")
    print("=" * 70)

if __name__ == "__main__":
    build_combined_dataset()
