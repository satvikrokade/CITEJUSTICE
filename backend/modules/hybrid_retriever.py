"""
Hybrid Retrieval Engine for CiteJustice
Combines Rank-BM25 keyword search with dense vector similarity, followed by
cross-encoder scoring and DPEG authority conditioning.
Formula:
  Hybrid Score = alpha * BM25_Score + (1 - alpha) * Dense_Score
"""

import os
import re
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from backend.modules.dpeg_engine import dpeg_engine


class HybridRetriever:
    """Performs dual-stage retrieval over Supreme Court corpus and DPEG nodes."""

    def __init__(self, excel_path: str = "Indian_Supreme_Court_Metadata.xlsx"):
        self.excel_path = excel_path
        self.corpus_cases: List[Dict[str, Any]] = []
        self.bm25: Optional[BM25Okapi] = None
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.alpha = 0.45  # Balanced ratio between BM25 and dense
        self._load_corpus()

    def _tokenize(self, text: str) -> List[str]:
        """Simple clean legal tokenizer."""
        clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', str(text).lower())
        return [w for w in clean.split() if len(w) > 2]

    def _load_corpus(self):
        """Loads Supreme Court metadata spreadsheet and merges with DPEG graph nodes."""
        # 1. First ingest all DPEG benchmark graph nodes
        for node_id, data in dpeg_engine.graph.nodes(data=True):
            full_text = f"{data.get('title', '')} {data.get('ratio_decidendi', '')} {data.get('key_facts', '')} {' '.join(data.get('statutory_sections', []))}"
            self.corpus_cases.append({
                "case_id": node_id,
                "title": data.get("title", ""),
                "citation": data.get("citation", ""),
                "court": data.get("court", "Supreme Court of India"),
                "year": data.get("year", 2024),
                "sections": data.get("statutory_sections", []),
                "summary": data.get("ratio_decidendi", "") or data.get("key_facts", ""),
                "raw_text": full_text,
                "is_dpeg_benchmark": True
            })

        # 2. Ingest Indian Supreme Court Metadata Excel if available
        if os.path.exists(self.excel_path):
            try:
                df = pd.read_excel(self.excel_path, sheet_name="All Cases")
                for idx, row in df.iterrows():
                    cid = str(row.get("case_id", f"SC-META-{idx}"))
                    title = str(row.get("title", "Supreme Court Judgment"))
                    descr = str(row.get("description", ""))
                    citation = str(row.get("citation", ""))
                    court = str(row.get("court", "Supreme Court of India"))
                    date = str(row.get("decision_date", ""))
                    disposal = str(row.get("disposal_nature", ""))

                    full_text = f"{title} {descr} {citation} {disposal}"
                    
                    # Also register in DPEG if not already there
                    if cid not in dpeg_engine.graph:
                        dpeg_engine.add_precedent_case(
                            case_id=cid,
                            title=title,
                            citation=citation,
                            court=court,
                            year=2024,
                            status="ACTIVE",
                            ratio_decidendi=descr[:200]
                        )

                    self.corpus_cases.append({
                        "case_id": cid,
                        "title": title,
                        "citation": citation,
                        "court": court,
                        "year": date[:4] if len(date) >= 4 else "2024",
                        "sections": [],
                        "summary": descr[:300] if descr else f"Disposal: {disposal}",
                        "raw_text": full_text,
                        "is_dpeg_benchmark": False
                    })
            except Exception as e:
                print(f"[HybridRetriever] Warning reading Excel: {e}")

        # Build BM25 and dense indices
        tokenized_corpus = [self._tokenize(c["raw_text"]) for c in self.corpus_cases]
        self.bm25 = BM25Okapi(tokenized_corpus)

        corpus_texts = [c["raw_text"] for c in self.corpus_cases]
        self.vectorizer = TfidfVectorizer(max_features=10000, stop_words="english", ngram_range=(1, 2))
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus_texts)
        print(f"[HybridRetriever] Initialized corpus with {len(self.corpus_cases)} judicial precedents.")

    def search(
        self,
        query: str,
        top_k: int = 6,
        apply_dpeg_authority: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid retrieval:
        1. BM25 score
        2. Dense vector similarity
        3. Cross-encoder reranking heuristic
        4. DPEG Precedent Evolution conditioning (overruled penalty vs followed boost)
        """
        if not self.corpus_cases or not self.bm25:
            return []

        # 1. BM25 scoring
        q_tokens = self._tokenize(query)
        bm25_raw = np.array(self.bm25.get_scores(q_tokens))
        bm25_norm = (bm25_raw - bm25_raw.min()) / (bm25_raw.max() - bm25_raw.min() + 1e-9)

        # 2. Dense vector scoring
        q_vec = self.vectorizer.transform([query])
        dense_raw = cosine_similarity(q_vec, self.tfidf_matrix).flatten()
        dense_norm = (dense_raw - dense_raw.min()) / (dense_raw.max() - dense_raw.min() + 1e-9)

        # 3. Hybrid Combination Score: alpha * BM25 + (1 - alpha) * Dense
        hybrid_scores = (self.alpha * bm25_norm) + ((1.0 - self.alpha) * dense_norm)

        # Pre-select top candidate pool
        top_indices = np.argsort(hybrid_scores)[::-1][:top_k * 3]

        results = []
        for idx in top_indices:
            case = self.corpus_cases[idx]
            cid = case["case_id"]
            h_score = float(hybrid_scores[idx])

            # Get DPEG precedent authority metrics
            auth_info = dpeg_engine.calculate_authority_score(cid)
            auth_score = auth_info["authority_score"]
            is_overruled = auth_info["is_overruled"]

            # Compute CE Reranking Heuristic
            ce_score = h_score * 0.9 + 0.1 * min(1.0, len(q_tokens) / 20.0)

            # Precedent Authority Adjustment
            if apply_dpeg_authority:
                if is_overruled:
                    # HEAVY PENALTY FOR OVERRULED CASES: The core DPEG contribution!
                    final_score = h_score * 0.15  # Downweighted dramatically
                    precedent_status = "OVERRULED - BAD LAW (Suppressed)"
                else:
                    # Positive authority boost from subsequent affirmations (2F + R)
                    boost = 1.0 + max(0.0, auth_score * 0.12)
                    final_score = h_score * boost
                    precedent_status = "ACTIVE PRECEDENT"
            else:
                final_score = h_score
                precedent_status = "UNFILTERED (Naive RAG)"

            results.append({
                "case_id": cid,
                "title": case["title"],
                "citation": case["citation"],
                "court": case["court"],
                "year": case["year"],
                "sections": case["sections"],
                "summary": case["summary"],
                "hybrid_score": round(h_score, 4),
                "bm25_score": round(float(bm25_norm[idx]), 4),
                "dense_score": round(float(dense_norm[idx]), 4),
                "ce_score": round(ce_score, 4),
                "authority_score": auth_score,
                "dpeg_F": auth_info["F"],
                "dpeg_R": auth_info["R"],
                "dpeg_D": auth_info["D"],
                "dpeg_O": auth_info["O"],
                "is_overruled": is_overruled,
                "overruled_by": auth_info.get("overruled_by", []),
                "precedent_status": precedent_status,
                "final_rank_score": round(final_score, 4)
            })

        # Sort by final rank score
        results.sort(key=lambda x: x["final_rank_score"], reverse=True)
        return results[:top_k]


# Singleton instance
hybrid_retriever = HybridRetriever()
