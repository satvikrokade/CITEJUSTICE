import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("HF_TOKEN")

dest_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "storage", "models", "InCaseLawBERT")
os.makedirs(dest_dir, exist_ok=True)

base_url = "https://huggingface.co/L-NLProc/NyayaAnumana-Transformer-Models/resolve/main/InCaseLaw/binary/multi/InCaseLawBERT_CJPE_ext_SCI_HCs_Tribunals_2019_multi"

files = [
    "config.json",
    "model.safetensors",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.txt"
]

headers = {"Authorization": f"Bearer {token}"} if token else {}

print(f"[*] Downloading InCaseLawBERT model files to: {dest_dir}")

for fname in files:
    target_path = os.path.join(dest_dir, fname)
    if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
        if fname != "model.safetensors" or os.path.getsize(target_path) > 400 * 1024 * 1024:
            print(f"[+] Already exists: {fname} ({os.path.getsize(target_path)} bytes)")
            continue

    url = f"{base_url}/{fname}"
    print(f"[>] Downloading {fname}...")
    resp = requests.get(url, headers=headers, stream=True, timeout=60)
    resp.raise_for_status()

    total_size = int(resp.headers.get("content-length", 0))
    downloaded = 0

    with open(target_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    pct = (downloaded / total_size) * 100
                    print(f"\r    {fname}: {downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB ({pct:.1f}%)", end="", flush=True)
    print(f"\n[+] Completed {fname}!")

print("[SUCCESS] All InCaseLawBERT model files are downloaded locally!")
