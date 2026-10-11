"""
CiteJustice - Phase 1 Batch Processing Script (for 2 Lakh Cases)
Leverages multiprocessing to process thousands of Supreme Court & High Court PDFs/texts
into structured Parquet records ready for Phase 2 (Vector Database & DPEG Graph).

Can be run locally or mounted on Google Colab / Kaggle free GPUs!
"""

import os
import sys
import glob
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.modules.phase1_parser import phase1_parser

def process_single_pdf(pdf_path: str) -> Dict[str, Any]:
    """Worker function to process a single PDF file."""
    try:
        with open(pdf_path, "rb") as f:
            content = f.read()
        record = phase1_parser.process_document(content, is_pdf=True)
        record["source_file"] = os.path.basename(pdf_path)
        return record
    except Exception as e:
        return {"source_file": os.path.basename(pdf_path), "error": str(e), "status": "FAILED"}

def run_batch_extraction(input_dir: str, output_jsonl: str = "phase1_extracted_corpus.jsonl", max_workers: int = 4):
    pdf_files = glob.glob(os.path.join(input_dir, "**/*.pdf"), recursive=True)
    total_files = len(pdf_files)
    print(f"[Phase 1 Batch Engine] Found {total_files} PDF judgments in {input_dir}")
    if total_files == 0:
        print("[!] No PDF files found to process.")
        return

    start_time = time.time()
    successful = 0
    failed = 0

    with open(output_jsonl, "w", encoding="utf-8") as out_f:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(process_single_pdf, pdf): pdf for pdf in pdf_files}
            for i, future in enumerate(as_completed(future_to_file), 1):
                res = future.result()
                if "error" in res:
                    failed += 1
                else:
                    successful += 1
                    out_f.write(json.dumps(res) + "\n")
                if i % 100 == 0 or i == total_files:
                    elapsed = time.time() - start_time
                    rate = i / elapsed if elapsed > 0 else 0
                    print(f"[{i}/{total_files}] Processed ({successful} ok, {failed} err) | Rate: {rate:.1f} cases/sec")

    print(f"\n[Phase 1 Batch Complete] Processed {successful} cases successfully into {output_jsonl} in {time.time()-start_time:.2f}s")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Batch Phase 1 Extractor for CiteJustice")
    parser.add_argument("--input_dir", type=str, default=".", help="Directory containing judgment PDFs")
    parser.add_argument("--output_file", type=str, default="phase1_extracted_corpus.jsonl", help="Output JSON Lines / Parquet file")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel worker processes")
    args = parser.parse_args()
    run_batch_extraction(args.input_dir, args.output_file, args.workers)
