"""
CiteJustice / NyayaAnumana - Continual Fine-Tuning Engine
Combines Pre-Trained InCaseLawBERT with our expanded corpus.

Usage:
  python scripts/train_fine_tune_bert.py              # auto-uses mega dataset if available
  python scripts/train_fine_tune_bert.py --epochs 3   # (edit defaults below)

Dataset priority:
  1. mega_train.jsonl   (from mega_dataset_builder.py -- recommended 10k+ records)
  2. combined_train.jsonl (from build_combined_dataset.py -- 2k records)
"""

import os
import sys
import json
import time
import torch
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup

# Ensure reproducibility
torch.manual_seed(42)

class LegalDataset(Dataset):
    def __init__(self, file_path, tokenizer, max_length=512, head_ratio=0.6):
        self.samples = []
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.head_tokens = int((max_length - 2) * head_ratio)
        self.tail_tokens = (max_length - 2) - self.head_tokens

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    self.samples.append(json.loads(line))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        item = self.samples[idx]
        text = str(item.get("text", ""))
        label = int(item.get("label", 0))

        tokens = self.tokenizer.tokenize(text)
        if len(tokens) > (self.max_length - 2):
            selected = tokens[:self.head_tokens] + tokens[-self.tail_tokens:]
        else:
            selected = tokens

        ids = [self.tokenizer.cls_token_id] + self.tokenizer.convert_tokens_to_ids(selected) + [self.tokenizer.sep_token_id]
        pad_len = self.max_length - len(ids)
        att = [1] * len(ids) + [0] * pad_len
        ids = ids + [self.tokenizer.pad_token_id] * pad_len

        return {
            "input_ids": torch.tensor(ids, dtype=torch.long),
            "attention_mask": torch.tensor(att, dtype=torch.long),
            "label": torch.tensor(label, dtype=torch.long)
        }

def run_fine_tuning(
    epochs: int = 2,
    batch_size: int = 4,
    grad_accum_steps: int = 4,
    learning_rate: float = 1.5e-5,
    max_train_samples: int = None   # None = use ALL available records
):
    print("=" * 70)
    print("   CITEJUSTICE: CONTINUAL FINE-TUNING ON INCASELAWBERT (HEAD-TAIL)")
    print("=" * 70)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fine_tuned_dir  = os.path.join(base_dir, "backend", "storage", "models", "InCaseLawBERT_FineTuned")
    base_raw_dir    = os.path.join(base_dir, "backend", "storage", "models", "InCaseLawBERT")
    
    # Priority: Continue from latest fine-tuned checkpoint if available
    model_source = fine_tuned_dir if os.path.exists(fine_tuned_dir) else base_raw_dir
    output_model_dir = fine_tuned_dir
    os.makedirs(output_model_dir, exist_ok=True)

    dataset_dir  = os.path.join(base_dir, "backend", "storage", "dataset")
    mega_train   = os.path.join(dataset_dir, "mega_train.jsonl")
    mega_val     = os.path.join(dataset_dir, "mega_val.jsonl")
    combo_train  = os.path.join(dataset_dir, "combined_train.jsonl")
    combo_val    = os.path.join(dataset_dir, "combined_val.jsonl")

    if os.path.exists(mega_train):
        train_file = mega_train
        val_file   = mega_val
        print("[+] MEGA DATASET detected -- using mega_train.jsonl (full corpus)")
    else:
        train_file = combo_train
        val_file   = combo_val
        print("[!] Using combined_train.jsonl")

    # 1. Device check
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[*] Compute Device : {device.upper()}")
    if device == "cuda":
        print(f"    GPU Model      : {torch.cuda.get_device_name(0)}")
        print(f"    Available VRAM : {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")

    # 2. Load Pre-Trained Model & Tokenizer
    print(f"[*] Step 1: Loading model foundation from '{model_source}'...")
    tokenizer = AutoTokenizer.from_pretrained(model_source)
    model = AutoModelForSequenceClassification.from_pretrained(model_source, num_labels=2)
    model.to(device)
    print(f"[+] Loaded model foundation successfully.")

    # 3. Prepare Datasets & Loaders with Head-Tail encoding
    print(f"[*] Step 2: Preparing expanded dataset with Head-Tail Legal Segmentation...")
    train_dataset = LegalDataset(train_file, tokenizer, max_length=512)
    val_dataset = LegalDataset(val_file, tokenizer, max_length=512)

    # Subset if requested
    if max_train_samples and max_train_samples < len(train_dataset):
        indices = list(range(max_train_samples))
        train_dataset = torch.utils.data.Subset(train_dataset, indices)
        val_dataset = torch.utils.data.Subset(val_dataset, list(range(min(200, len(val_dataset)))))

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    print(f"[+] Training Set   : {len(train_dataset)} cases")
    print(f"[+] Validation Set : {len(val_dataset)} cases")

    # 4. Class weighting & Optimizer
    labels_list = [train_dataset[i]["label"].item() for i in range(min(500, len(train_dataset)))]
    c0 = max(1, labels_list.count(0))
    c1 = max(1, labels_list.count(1))
    weights = torch.tensor([c1 / (c0 + c1) * 2.0, c0 / (c0 + c1) * 2.0], device=device)
    loss_fn = torch.nn.CrossEntropyLoss(weight=weights)

    optimizer = AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)
    total_steps = (len(train_loader) // grad_accum_steps) * epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=20, num_training_steps=max(1, total_steps))
    use_amp = (device == "cuda")
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    # 5. Training Loop
    print("\n" + "-" * 70)
    print(f"[*] Starting Continual Fine-Tuning ({epochs} Epoch(s) | Effective Batch Size: {batch_size * grad_accum_steps} | FP16 AMP: {use_amp})")
    print("-" * 70)

    start_time = time.time()
    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        step_count = 0
        optimizer.zero_grad()

        for step, batch in enumerate(train_loader, 1):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["label"].to(device)

            with torch.amp.autocast("cuda", enabled=use_amp):
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                loss = loss_fn(outputs.logits, labels) / grad_accum_steps

            scaler.scale(loss).backward()
            running_loss += loss.item() * grad_accum_steps
            step_count += 1

            if step % grad_accum_steps == 0 or step == len(train_loader):
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer)
                scaler.update()
                scheduler.step()
                optimizer.zero_grad()

            if step % 25 == 0 or step == len(train_loader):
                avg_step_loss = running_loss / step_count
                pct = (step / len(train_loader)) * 100
                print(f"    Epoch {epoch}/{epochs} | Step {step}/{len(train_loader)} ({pct:.0f}%) | Current Loss: {avg_step_loss:.4f}", flush=True)

        # Validation Phase
        model.eval()
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                labels = batch["label"].to(device)

                with torch.amp.autocast("cuda", enabled=use_amp):
                    outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                preds = torch.argmax(outputs.logits, dim=-1)
                val_correct += (preds == labels).sum().item()
                val_total += labels.size(0)

        val_acc = (val_correct / val_total) * 100 if val_total > 0 else 0
        print(f"\n[+] Epoch {epoch} Complete! Validation Accuracy: {val_acc:.2f}% | Elapsed: {time.time() - start_time:.1f}s", flush=True)
        print("-" * 70, flush=True)

    # 6. Save Fine-Tuned Model Weights & Tokenizer
    print(f"[*] Step 3: Saving Fine-Tuned Model to: {output_model_dir} ...", flush=True)
    model.save_pretrained(output_model_dir)
    tokenizer.save_pretrained(output_model_dir)

    metadata = {
        "base_model": "L-NLProc/InCaseLawBERT (Pre-trained on 702,945 Indian cases)",
        "continual_fine_tuning": "Combined Local Supreme Court + L-NLProc/PredEx",
        "train_samples": len(train_dataset),
        "val_samples": len(val_dataset),
        "dataset_size": len(train_dataset) + len(val_dataset),
        "epochs": epochs,
        "device": device.upper(),
        "validation_accuracy": f"{val_acc:.2f}%",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(os.path.join(output_model_dir, "training_meta.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # 7. Auto-update TRAINING_HISTORY.md
    try:
        history_md_path = os.path.join(base_dir, "TRAINING_HISTORY.md")
        history_json_path = os.path.join(dataset_dir, "training_history.json")

        # Load or init JSON log
        history_records = []
        if os.path.exists(history_json_path):
            try:
                with open(history_json_path, "r", encoding="utf-8") as jf:
                    history_records = json.load(jf)
            except Exception:
                history_records = []

        run_id = len(history_records) + 1
        record = {
            "run_id": run_id,
            "timestamp": metadata["timestamp"],
            "base_model": "InCaseLawBERT (702k Base)",
            "fine_tune_dataset": "Mega Dataset (Local + PredEx)",
            "train_cases": len(train_dataset),
            "val_cases": len(val_dataset),
            "total_cases": len(train_dataset) + len(val_dataset),
            "epochs": epochs,
            "device": device.upper(),
            "validation_accuracy": f"{val_acc:.2f}%",
            "status": "Completed"
        }
        history_records.append(record)
        with open(history_json_path, "w", encoding="utf-8") as jf:
            json.dump(history_records, jf, indent=2)

        record["trained_by"] = "Satvik"
        # Append new row to markdown table
        new_row = f"| **{run_id}** | {record['timestamp']} | {record['base_model']} | {record['fine_tune_dataset']} | {record['train_cases']:,} | {record['val_cases']:,} | {record['total_cases']:,} | {record['epochs']} | {record['device']} | **{record['validation_accuracy']}** | **Satvik** | Completed |\n"
        
        if os.path.exists(history_md_path):
            with open(history_md_path, "r", encoding="utf-8") as mf:
                content = mf.read()
            # If there is a running row, replace it or append
            if "*Training in Progress...*" in content:
                content = content.replace("| *Training in Progress...* | **RUNNING** |", f"**{record['validation_accuracy']}** | Completed |")
                with open(history_md_path, "w", encoding="utf-8") as mf:
                    mf.write(content)
            else:
                with open(history_md_path, "a", encoding="utf-8") as mf:
                    mf.write(new_row)
        print(f"[+] Updated training log: {history_md_path}")
    except Exception as e:
        print(f"[!] Warning: Could not update TRAINING_HISTORY.md: {e}")

    print(f"[SUCCESS] Combined Fine-Tuning Completed in {time.time() - start_time:.1f}s!")
    print(f"[+] Output Model Saved at: {output_model_dir}")
    print("=" * 70)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Continual Fine-Tuning Engine for InCaseLawBERT")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size per step")
    parser.add_argument("--grad_accum_steps", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--learning_rate", type=float, default=2e-5, help="Learning rate")
    parser.add_argument("--max_train_samples", type=int, default=None, help="Max train samples limit (None for all)")
    args = parser.parse_args()

    run_fine_tuning(
        epochs=args.epochs,
        batch_size=args.batch_size,
        grad_accum_steps=args.grad_accum_steps,
        learning_rate=args.learning_rate,
        max_train_samples=args.max_train_samples
    )
