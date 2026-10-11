"""
CiteJustice / NyayaAnumana - InCaseLawBERT Inference & Outcome Predictor
Runs local evaluation using the official COLING 2025 InCaseLawBERT checkpoint
trained across Supreme Court, High Courts, and Tribunals.
"""

import os
import sys
import time
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

def run_nyayaanumana_inference():
    print("=" * 70)
    print("      NYAYAANUMANA / INCASELAWBERT LEGAL VERDICT INFERENCE")
    print("=" * 70)

    model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "storage", "models", "InCaseLawBERT")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[*] Compute Target: {device.upper()}")
    if device == "cuda":
        print(f"    GPU Device: {torch.cuda.get_device_name(0)}")
        print(f"    Available VRAM: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")

    print(f"[*] Loading model from local storage: {model_dir} ...")
    start_load = time.time()
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    model.to(device)
    model.eval()
    print(f"[+] Model loaded in {time.time() - start_load:.2f} seconds.")

    # Labels: 0 = Dismissed (Rejected), 1 = Allowed (Accepted / Relief Granted)
    label_map = {
        0: "DISMISSED (Appeal Rejected / Conviction Sustained)",
        1: "ALLOWED (Appeal Accepted / Relief Granted / Conviction Modified)"
    }
    
    test_cases = [
        {
            "title": "Criminal Appeal: Sudden Quarrel & Heat of Passion",
            "statute": "Section 302 IPC / Exception 4 to Section 300 (BNS 103 / 105)",
            "facts": (
                "The appellant and the deceased were neighbors who entered into an impromptu altercation "
                "regarding irrigation water flow. In the heat of the moment, the appellant picked up a wooden stick "
                "lying nearby and struck a single blow causing death. There was no premeditation, no prior enmity, "
                "and no weapon was carried beforehand. The appellant did not act in a cruel or unusual manner. "
                "The appellant prays for alteration of conviction from murder to culpable homicide not amounting to murder."
            )
        },
        {
            "title": "Criminal Appeal: Premeditated Ambush & Brutal Assault",
            "statute": "Section 302 / 34 IPC (BNS 103)",
            "facts": (
                "The accused appellants armed with deadly sharp-edged swords lay in wait behind the sugarcane field "
                "with the common intention to eliminate the victim due to old electoral rivalry. As the victim "
                "passed on his motorcycle, the appellants ambushed him and inflicted 14 deep incised wounds on "
                "vital parts of the body, leading to instantaneous death. The eyewitness testimony of PW-1 and PW-2 "
                "is corroborated by recovery of blood-stained weapons and medical post-mortem report."
            )
        },
        {
            "title": "Bail Application under Section 439 CrPC (BNSS 483)",
            "statute": "NDPS Act / CrPC 439 / Section 37 Conditions",
            "facts": (
                "The petitioner is an undertrial prisoner incarcerated for over 3 years without trial commencement. "
                "The contraband alleged to be recovered from personal search was below commercial quantity. "
                "The co-accused having identical role has already been enlarged on regular bail by this Hon'ble Court. "
                "The petitioner has clean antecedents and is ready to furnish local solvent sureties."
            )
        }
    ]

    print("\n" + "-" * 70)
    print("                     EVALUATING TEST CASES")
    print("-" * 70)

    for idx, c in enumerate(test_cases, 1):
        print(f"\n[Case #{idx}]: {c['title']}")
        print(f"Statute / Context: {c['statute']}")
        print(f"Factual Matrix: \"{c['facts'][:140]}...\"")
        
        t0 = time.time()
        inputs = tokenizer(
            c['facts'],
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        ).to(device)

        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1).squeeze().tolist()
            predicted_class = int(torch.argmax(logits, dim=-1).item())

        elapsed_ms = (time.time() - t0) * 1000
        prob_allowed = probs[1] if len(probs) > 1 else probs[0]
        prob_dismissed = probs[0] if len(probs) > 1 else 1 - probs[0]

        verdict_str = label_map.get(predicted_class, f"Class {predicted_class}")
        confidence = max(probs) * 100

        print(f"\n   >>> PREDICTED VERDICT : {verdict_str}")
        print(f"   >>> CONFIDENCE SCORE  : {confidence:.2f}%")
        print(f"   >>> PROBABILITY SPREAD: Allowed = {prob_allowed*100:.2f}% | Dismissed = {prob_dismissed*100:.2f}%")
        print(f"   >>> INFERENCE LATENCY : {elapsed_ms:.1f} ms")
        print("-" * 70)

if __name__ == "__main__":
    run_nyayaanumana_inference()
