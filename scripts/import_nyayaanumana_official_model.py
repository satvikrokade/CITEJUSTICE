"""
Import official pre-trained NyayaAnumana InCaseLawBERT model directly from Hugging Face:
Repository: L-NLProc/NyayaAnumana-Transformer-Models
Subfolder: InCaseLaw/binary/multi/InCaseLawBERT_SCI_HCs_multi_epoch_2
Target: backend/storage/models/InCaseLawBERT_FineTuned/
"""

import os
import shutil
import json
import datetime
from huggingface_hub import hf_hub_download

REPO_ID = "L-NLProc/NyayaAnumana-Transformer-Models"
SUBFOLDER = "InCaseLaw/binary/multi/InCaseLawBERT_SCI_HCs_multi_epoch_2"
TOKEN = os.getenv("HF_TOKEN") or None
TARGET_DIR = "backend/storage/models/InCaseLawBERT_FineTuned"
BACKUP_DIR = "backend/storage/models/InCaseLawBERT_FineTuned_Run3_Local"

FILES_TO_DOWNLOAD = [
    "config.json",
    "model.safetensors",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.txt"
]

def main():
    print("=" * 70)
    print("   IMPORTING OFFICIAL NYAYAANUMANA FINE-TUNED MODEL")
    print("=" * 70)

    # 1. Backup existing local Run 3 checkpoint
    if os.path.exists(TARGET_DIR) and not os.path.exists(BACKUP_DIR):
        print(f"[*] Backing up local Run 3 model to '{BACKUP_DIR}'...")
        shutil.copytree(TARGET_DIR, BACKUP_DIR)
        print("[+] Backup created successfully.")

    os.makedirs(TARGET_DIR, exist_ok=True)

    # 2. Download official weights from Hugging Face
    print(f"\n[*] Connecting to Hugging Face: {REPO_ID} [{SUBFOLDER}]...")
    for filename in FILES_TO_DOWNLOAD:
        full_repo_path = f"{SUBFOLDER}/{filename}"
        print(f" -> Downloading {filename}...")
        downloaded_file = hf_hub_download(
            repo_id=REPO_ID,
            filename=full_repo_path,
            token=TOKEN
        )
        dest_path = os.path.join(TARGET_DIR, filename)
        shutil.copyfile(downloaded_file, dest_path)
        print(f"    [+] Saved to {dest_path}")

    # 3. Write metadata
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta = {
        "model_name": "L-NLProc/NyayaAnumana-InCaseLawBERT (SCI + HCs Multi)",
        "hf_repository": REPO_ID,
        "hf_subfolder": SUBFOLDER,
        "dataset": "NyayaAnumana (702,945 Pre-processed Indian Supreme Court + High Court Cases)",
        "architecture": "InCaseLawBERT SequenceClassification (Binary: 0=Dismissed, 1=Allowed)",
        "paper_citation": "NyayaAnumana & INLegalLlama (COLING 2025)",
        "validation_accuracy": "78.40%",
        "f1_score": "90.20%",
        "status": "Official Pre-Trained Benchmark Active",
        "imported_at": now_str
    }
    with open(os.path.join(TARGET_DIR, "training_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print("\n[+] Success! Official NyayaAnumana fine-tuned model successfully deployed to:")
    print(f"    {TARGET_DIR}")

if __name__ == "__main__":
    main()
