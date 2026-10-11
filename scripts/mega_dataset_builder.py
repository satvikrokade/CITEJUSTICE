"""
CiteJustice - MEGA COMBINED DATASET BUILDER
============================================================
Combines ALL available data sources into one large fine-tuning corpus:

  Layer 1 (Pre-trained):     InCaseLawBERT base -- 702,945 Indian cases
  Layer 2 (Local Excel):     Indian_Supreme_Court_Metadata.xlsx -- 897 rows
  Layer 3 (HF PredEx):       L-NLProc/PredEx -- ~6,000+ cases (all splits)
  Layer 4 (HF ILDC):         Exploration-Lab/ILDC_expert -- ~5,000 cases
  Layer 5 (HF NyayaAnumana): L-NLProc/NyayaAnumana -- ~10,000+ cases
  Layer 6 (HF IndianLegal):  law-ai/Indian-Legal-Dataset if accessible

Target: 10,000-20,000 labeled fine-tuning samples => 85-90% accuracy
Current: 2,057 samples => 59% accuracy

Run: python scripts/mega_dataset_builder.py
"""

import os, sys, json, random, time, re
import pandas as pd
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

OUTPUT_DIR = "backend/storage/dataset"
TRAIN_FILE = os.path.join(OUTPUT_DIR, "mega_train.jsonl")
VAL_FILE   = os.path.join(OUTPUT_DIR, "mega_val.jsonl")
STATS_FILE = os.path.join(OUTPUT_DIR, "mega_dataset_stats.json")

HF_TOKEN = os.getenv("HF_TOKEN", "")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def banner(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def clean_text(t):
    if not t:
        return ""
    t = str(t).strip()
    t = re.sub(r'\s+', ' ', t)
    return t[:2000]


def label_from_disposal(disposal_str):
    """Map Indian court disposal_nature to binary label (1=Allowed, 0=Dismissed)."""
    d = str(disposal_str).lower().strip()
    if any(k in d for k in ["allowed", "granted", "partly allowed", "succeeded", "quashed", "modified"]):
        return 1
    if any(k in d for k in ["dismissed", "rejected", "denied", "upheld conviction", "refused"]):
        return 0
    return None


def make_record(title, text, label, source):
    return {
        "case_title": clean_text(title),
        "text": clean_text(text),
        "label": int(label),
        "source": source
    }


# ─── Source 1: Local Supreme Court Excel ──────────────────────────────────

def load_local_excel(path="Indian_Supreme_Court_Metadata.xlsx"):
    banner("SOURCE 1: Local Indian_Supreme_Court_Metadata.xlsx")
    records = []
    if not os.path.exists(path):
        print(f"[!] File not found: {path}")
        return records

    df = pd.read_excel(path, sheet_name="All Cases")
    print(f"[+] Loaded {len(df)} rows from Excel")

    for _, row in df.iterrows():
        title  = str(row.get("title", "")).strip()
        desc   = str(row.get("description", "")).strip()
        disp   = str(row.get("disposal_nature", "")).strip()

        if len(desc) < 60:
            continue
        label = label_from_disposal(disp)
        if label is None:
            continue

        text = f"Matter: {title}. Disposal: {disp}. {desc}"
        records.append(make_record(title, text, label, "local_excel_supreme_court"))

    print(f"[OK] Extracted {len(records)} labeled records from Excel")
    return records


# ─── Source 2: HuggingFace L-NLProc/PredEx (ALL splits) ──────────────────

def load_predex_all():
    banner("SOURCE 2: HuggingFace L-NLProc/PredEx (train + test + validation)")
    records = []
    try:
        from datasets import load_dataset
        token = HF_TOKEN or None

        for split in ["train", "test", "validation"]:
            try:
                print(f"  [*] Loading PredEx split: {split}...")
                ds = load_dataset("L-NLProc/PredEx", split=split,
                                  token=token, trust_remote_code=True)
                split_count = 0
                for item in ds:
                    text      = item.get("Input", item.get("text", ""))
                    label_raw = str(item.get("Label", item.get("label", ""))).strip()
                    title     = item.get("Case Name", item.get("title", ""))

                    if not text or len(str(text)) < 80:
                        continue
                    if str(label_raw) not in ["0", "1"]:
                        continue

                    records.append(make_record(title, text, int(str(label_raw)), "HF_PredEx_" + split))
                    split_count += 1
                print(f"  [+] {split}: {split_count} records")
            except Exception as e:
                print(f"  [!] PredEx {split} failed: {e}")

    except ImportError:
        print("[!] datasets library not installed -- run: pip install datasets")

    print(f"[OK] Total PredEx records: {len(records)}")
    return records


# ─── Source 3: Exploration-Lab/ILDC_expert ────────────────────────────────

def load_ildc():
    banner("SOURCE 3: HuggingFace Exploration-Lab/ILDC_expert")
    records = []
    try:
        from datasets import load_dataset
        token = HF_TOKEN or None

        for split in ["train", "dev", "test"]:
            try:
                print(f"  [*] Loading ILDC split: {split}...")
                ds = load_dataset("Exploration-Lab/ILDC_expert", split=split,
                                  token=token, trust_remote_code=True)
                split_count = 0
                for item in ds:
                    text  = item.get("text", item.get("document", item.get("judgment", "")))
                    label = item.get("label", item.get("Label", None))

                    if not text or len(str(text)) < 80:
                        continue
                    if label not in [0, 1]:
                        continue

                    title = item.get("case_id", item.get("title", "ILDC Case"))
                    records.append(make_record(title, text, int(label), "HF_ILDC_" + split))
                    split_count += 1
                print(f"  [+] {split}: {split_count} records")
            except Exception as e:
                print(f"  [!] ILDC {split} failed: {e}")

        print(f"[OK] Total ILDC records: {len(records)}")
    except ImportError:
        print("[!] datasets library not installed")
    return records


# ─── Source 4: L-NLProc/NyayaAnumana ─────────────────────────────────────

def load_nyayaanumana(max_per_split=5000):
    banner("SOURCE 4: HuggingFace L-NLProc/NyayaAnumana")
    records = []
    try:
        from datasets import load_dataset
        token = HF_TOKEN or None

        for split in ["train", "test"]:
            try:
                print(f"  [*] Loading NyayaAnumana split: {split} (max {max_per_split})...")
                ds = load_dataset("L-NLProc/NyayaAnumana", split=split,
                                  token=token, trust_remote_code=True,
                                  streaming=True)
                count = 0
                for item in ds:
                    text  = item.get("text", item.get("Input", ""))
                    label = item.get("label", item.get("Label", None))

                    if not text or len(str(text)) < 80:
                        continue
                    if str(label) not in ["0", "1"]:
                        continue

                    title = item.get("title", item.get("Case Name", "NyayaAnumana"))
                    records.append(make_record(title, text, int(str(label)), "HF_NyayaAnumana_" + split))
                    count += 1
                    if count >= max_per_split:
                        break
                print(f"  [+] {split}: {count} records loaded")
            except Exception as e:
                print(f"  [!] NyayaAnumana {split} failed: {e}")

        print(f"[OK] Total NyayaAnumana records: {len(records)}")
    except ImportError:
        print("[!] datasets library not installed")
    return records


# ─── Source 5: law-ai/Indian-Legal-Dataset (bonus) ───────────────────────

def load_indian_legal_dataset(max_records=3000):
    banner("SOURCE 5: law-ai/Indian-Legal-Dataset (bonus if accessible)")
    records = []
    try:
        from datasets import load_dataset
        token = HF_TOKEN or None
        ds = load_dataset("law-ai/Indian-Legal-Dataset", split="train",
                          token=token, trust_remote_code=True, streaming=True)
        count = 0
        for item in ds:
            text  = item.get("judgment", item.get("text", ""))
            label = item.get("label", None)
            if not text or len(str(text)) < 80 or str(label) not in ["0", "1"]:
                continue
            title = item.get("title", "Indian Legal")
            records.append(make_record(title, text, int(str(label)), "HF_IndianLegal"))
            count += 1
            if count >= max_records:
                break
        print(f"[OK] law-ai/Indian-Legal-Dataset: {len(records)} records loaded")
    except Exception as e:
        print(f"[!] law-ai/Indian-Legal-Dataset not available: {e}")
    return records


# ─── Master Builder ────────────────────────────────────────────────────────

def build_mega_dataset():
    banner("CITEJUSTICE MEGA DATASET BUILDER -- All Sources Combined")
    print(f"  HuggingFace Token : {'SET (OK)' if HF_TOKEN else 'NOT SET -- some sources may fail'}")
    print(f"  Output directory  : {OUTPUT_DIR}")

    all_records  = []
    source_stats = {}

    sources = [
        ("Local Excel SC",          load_local_excel),
        ("HF PredEx (all splits)",  load_predex_all),
        ("HF ILDC Expert",          load_ildc),
        ("HF NyayaAnumana",         load_nyayaanumana),
        ("HF Indian-Legal",         load_indian_legal_dataset),
    ]

    for name, fn in sources:
        t0 = time.time()
        try:
            recs = fn()
            all_records.extend(recs)
            source_stats[name] = {"count": len(recs), "time_s": round(time.time() - t0, 1)}
            print(f"\n  [{name}] => {len(recs)} records  |  cumulative total: {len(all_records)}\n")
        except Exception as e:
            print(f"\n  [ERROR] {name} failed: {e}\n")
            source_stats[name] = {"count": 0, "error": str(e)}

    # ── Deduplicate by first 200 chars of text ────────────────────────────
    banner("DEDUPLICATION & BALANCING")
    seen = set()
    unique_records = []
    for r in all_records:
        key = r["text"][:200]
        if key not in seen:
            seen.add(key)
            unique_records.append(r)
    print(f"  Before dedup : {len(all_records):,}")
    print(f"  After  dedup : {len(unique_records):,}")

    # ── Class balance ─────────────────────────────────────────────────────
    allowed   = sum(1 for r in unique_records if r["label"] == 1)
    dismissed = len(unique_records) - allowed
    print(f"\n  Class distribution:")
    print(f"    Allowed   (1): {allowed:,}  ({allowed/len(unique_records)*100:.1f}%)")
    print(f"    Dismissed (0): {dismissed:,}  ({dismissed/len(unique_records)*100:.1f}%)")

    # ── Shuffle and split 85% / 15% ──────────────────────────────────────
    random.seed(42)
    random.shuffle(unique_records)
    total   = len(unique_records)
    split   = int(total * 0.85)
    train_r = unique_records[:split]
    val_r   = unique_records[split:]

    # ── Write JSONL files ─────────────────────────────────────────────────
    banner("WRITING OUTPUT FILES")
    with open(TRAIN_FILE, "w", encoding="utf-8") as f:
        for r in train_r:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(VAL_FILE, "w", encoding="utf-8") as f:
        for r in val_r:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ── Save statistics JSON ──────────────────────────────────────────────
    stats = {
        "total_unique_records": total,
        "train_records": len(train_r),
        "val_records": len(val_r),
        "class_allowed": allowed,
        "class_dismissed": dismissed,
        "source_breakdown": source_stats,
        "output_train": TRAIN_FILE,
        "output_val": VAL_FILE,
        "built_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    # ── Final Summary ─────────────────────────────────────────────────────
    banner("FINAL SUMMARY")
    print(f"\n  TOTAL UNIQUE RECORDS : {total:,}")
    print(f"  TRAIN  (85%)         : {len(train_r):,}")
    print(f"  VALID  (15%)         : {len(val_r):,}")
    print(f"\n  Per-source breakdown:")
    for src, s in source_stats.items():
        print(f"    {src:38s}: {s.get('count', 0):,}")
    print(f"\n  Output files:")
    print(f"    {TRAIN_FILE}")
    print(f"    {VAL_FILE}")
    print(f"    {STATS_FILE}")
    print("\n  NEXT STEP --> Run full fine-tuning:")
    print("    python scripts/train_fine_tune_bert.py")
    print("\n  Expected accuracy targets:")
    print("    2,000   records => ~59%  (current)")
    print("    5,000   records => ~70-74%")
    print("    10,000  records => ~78-82%")
    print("    20,000  records => ~85-90%")
    print("="*70)
    return stats


if __name__ == "__main__":
    build_mega_dataset()
