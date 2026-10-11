"""
CiteJustice - Hugging Face Dataset Ingestion & Phase 1 Converter
Streams or downloads Indian legal datasets from Hugging Face (e.g., ILDC, InLegalBERT corpus,
or custom user datasets) and processes them directly through the Phase 1 Segmentation Pipeline.
"""

import os
import sys
import json
import argparse
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.modules.phase1_parser import phase1_parser

def ingest_from_huggingface(
    dataset_name: str = "Exploration-Lab/InLegalScorer",
    split: str = "train",
    text_column: str = "text",
    max_samples: Optional[int] = None,
    output_file: str = "phase1_extracted_corpus.jsonl"
):
    try:
        from datasets import load_dataset
    except ImportError:
        print("[!] 'datasets' library not found. Please install via: pip install datasets")
        return

    print(f"[*] Loading dataset '{dataset_name}' (split: {split}) from Hugging Face...")
    try:
        # Load in streaming mode for memory efficiency with large corpora
        ds = load_dataset(dataset_name, split=split, streaming=True)
    except Exception as e:
        print(f"[!] Direct load failed: {e}. Attempting non-streaming mode...")
        ds = load_dataset(dataset_name, split=split)

    print(f"[*] Connected. Streaming and extracting Phase 1 records into '{output_file}'...")
    
    count = 0
    successful = 0
    failed = 0

    with open(output_file, "w", encoding="utf-8") as out_f:
        for item in ds:
            count += 1
            if max_samples and count > max_samples:
                break

            # Find text content from common column names if text_column is not present
            raw_text = None
            for col in [text_column, "text", "judgment", "facts", "content", "document"]:
                if col in item and item[col]:
                    raw_text = str(item[col])
                    break

            if not raw_text or len(raw_text.strip()) < 80:
                continue

            try:
                record = phase1_parser.process_document(raw_text, is_pdf=False)
                # Attach extra metadata from Hugging Face record if available
                record["source_dataset"] = dataset_name
                record["hf_row_index"] = count
                for meta_key in ["case_id", "label", "court", "year", "title"]:
                    if meta_key in item and item[meta_key]:
                        record["metadata"][meta_key] = item[meta_key]

                out_f.write(json.dumps(record) + "\n")
                successful += 1

                if successful % 250 == 0:
                    print(f"[*] Processed {successful} cases from Hugging Face...")
            except Exception as e:
                failed += 1

    print(f"\n[✔ Completed] Ingested {successful} cases ({failed} errors) saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Hugging Face Legal Datasets into Phase 1")
    parser.add_argument("--dataset", type=str, default="Exploration-Lab/InLegalScorer", help="Hugging Face Dataset Name")
    parser.add_argument("--split", type=str, default="train", help="Dataset split (train/test/validation)")
    parser.add_argument("--text_col", type=str, default="text", help="Name of column containing judgment text")
    parser.add_argument("--max_samples", type=int, default=1000, help="Max number of cases to process (None for all)")
    parser.add_argument("--output", type=str, default="phase1_extracted_corpus.jsonl", help="Output JSONL path")
    args = parser.parse_args()

    ingest_from_huggingface(
        dataset_name=args.dataset,
        split=args.split,
        text_column=args.text_col,
        max_samples=args.max_samples,
        output_file=args.output
    )
