"""
Statutory Cross-Mapping Engine for CiteJustice
Bridges historical statutes (IPC 1860, CrPC 1973, IEA 1872) with modern Indian criminal law
(Bharatiya Nyaya Sanhita 2023 [BNS], Bharatiya Nagarik Suraksha Sanhita 2023 [BNSS], Bharatiya Sakshya Adhiniyam 2023 [BSA]).
"""

import re
from typing import Dict, List, Optional, Any

# Primary Mapping Database: Historical -> Modern
STATUTORY_MAP = {
    # IPC -> BNS (Bharatiya Nyaya Sanhita 2023)
    "IPC 302": {
        "modern_act": "BNS",
        "modern_section": "103(1)",
        "offense": "Murder / Punishment for Murder",
        "historical_act": "IPC",
        "historical_section": "302",
        "bailable": "Non-Bailable",
        "cognizable": "Cognizable",
        "court_trial": "Court of Session",
        "quantum": "Death or imprisonment for life, and fine"
    },
    "IPC 304": {
        "modern_act": "BNS",
        "modern_section": "105",
        "offense": "Culpable Homicide not amounting to Murder",
        "historical_act": "IPC",
        "historical_section": "304",
        "bailable": "Non-Bailable",
        "cognizable": "Cognizable",
        "court_trial": "Court of Session",
        "quantum": "Imprisonment for life or up to 10 years, and fine"
    },
    "IPC 304A": {
        "modern_act": "BNS",
        "modern_section": "106",
        "offense": "Causing death by rash or negligent act",
        "historical_act": "IPC",
        "historical_section": "304A",
        "bailable": "Bailable",
        "cognizable": "Cognizable",
        "court_trial": "Magistrate of First Class",
        "quantum": "Imprisonment up to 5 years, and fine"
    },
    "IPC 307": {
        "modern_act": "BNS",
        "modern_section": "109",
        "offense": "Attempt to Murder",
        "historical_act": "IPC",
        "historical_section": "307",
        "bailable": "Non-Bailable",
        "cognizable": "Cognizable",
        "court_trial": "Court of Session",
        "quantum": "Imprisonment up to 10 years, or life imprisonment if hurt caused"
    },
    "IPC 420": {
        "modern_act": "BNS",
        "modern_section": "318(4)",
        "offense": "Cheating and dishonestly inducing delivery of property",
        "historical_act": "IPC",
        "historical_section": "420",
        "bailable": "Non-Bailable",
        "cognizable": "Cognizable",
        "court_trial": "Magistrate of First Class",
        "quantum": "Imprisonment up to 7 years, and fine"
    },
    "IPC 376": {
        "modern_act": "BNS",
        "modern_section": "64",
        "offense": "Rape / Punishment for Rape",
        "historical_act": "IPC",
        "historical_section": "376",
        "bailable": "Non-Bailable",
        "cognizable": "Cognizable",
        "court_trial": "Court of Session",
        "quantum": "Rigorous imprisonment not less than 10 years extending to life"
    },
    "IPC 120B": {
        "modern_act": "BNS",
        "modern_section": "61",
        "offense": "Criminal Conspiracy",
        "historical_act": "IPC",
        "historical_section": "120B",
        "bailable": "According to main offense",
        "cognizable": "According to main offense",
        "court_trial": "According to main offense",
        "quantum": "Same as abetment of the offense"
    },
    "IPC 34": {
        "modern_act": "BNS",
        "modern_section": "3(5)",
        "offense": "Acts done by several persons in furtherance of common intention",
        "historical_act": "IPC",
        "historical_section": "34",
        "bailable": "Joint Liability principle",
        "cognizable": "Joint Liability",
        "court_trial": "Court trying principal offense",
        "quantum": "Co-extensive liability with principal offender"
    },
    "IPC 498A": {
        "modern_act": "BNS",
        "modern_section": "85",
        "offense": "Husband or relative of husband of a woman subjecting her to cruelty",
        "historical_act": "IPC",
        "historical_section": "498A",
        "bailable": "Non-Bailable",
        "cognizable": "Cognizable",
        "court_trial": "Magistrate of First Class",
        "quantum": "Imprisonment up to 3 years, and fine"
    },
    "IPC 506": {
        "modern_act": "BNS",
        "modern_section": "351(2)",
        "offense": "Criminal Intimidation",
        "historical_act": "IPC",
        "historical_section": "506",
        "bailable": "Bailable",
        "cognizable": "Non-Cognizable",
        "court_trial": "Any Magistrate",
        "quantum": "Imprisonment up to 2 years, or fine, or both"
    },
    "IPC 323": {
        "modern_act": "BNS",
        "modern_section": "115(2)",
        "offense": "Voluntarily causing hurt",
        "historical_act": "IPC",
        "historical_section": "323",
        "bailable": "Bailable",
        "cognizable": "Non-Cognizable",
        "court_trial": "Any Magistrate",
        "quantum": "Imprisonment up to 1 year, or fine up to Rs 1,000, or both"
    },
    "IPC 326": {
        "modern_act": "BNS",
        "modern_section": "118(1)",
        "offense": "Voluntarily causing grievous hurt by dangerous weapons or means",
        "historical_act": "IPC",
        "historical_section": "326",
        "bailable": "Non-Bailable",
        "cognizable": "Cognizable",
        "court_trial": "Magistrate of First Class",
        "quantum": "Imprisonment for life, or up to 10 years, and fine"
    },

    # CrPC -> BNSS (Bharatiya Nagarik Suraksha Sanhita 2023)
    "CrPC 482": {
        "modern_act": "BNSS",
        "modern_section": "528",
        "offense": "Inherent powers of High Court to prevent abuse of court process",
        "historical_act": "CrPC",
        "historical_section": "482",
        "bailable": "Procedural Inherent Jurisdiction",
        "cognizable": "Procedural",
        "court_trial": "High Court",
        "quantum": "Quashing of FIR / Criminal Proceedings"
    },
    "CrPC 438": {
        "modern_act": "BNSS",
        "modern_section": "482",
        "offense": "Direction for grant of bail to person apprehending arrest (Anticipatory Bail)",
        "historical_act": "CrPC",
        "historical_section": "438",
        "bailable": "Anticipatory Bail Jurisdiction",
        "cognizable": "Procedural",
        "court_trial": "Sessions Court / High Court",
        "quantum": "Pre-arrest protective bail order"
    },
    "CrPC 439": {
        "modern_act": "BNSS",
        "modern_section": "483",
        "offense": "Special powers of High Court or Court of Session regarding regular bail",
        "historical_act": "CrPC",
        "historical_section": "439",
        "bailable": "Regular Bail Jurisdiction",
        "cognizable": "Procedural",
        "court_trial": "Sessions Court / High Court",
        "quantum": "Regular Bail / Release from custody"
    },
    "CrPC 154": {
        "modern_act": "BNSS",
        "modern_section": "173",
        "offense": "Information in cognizable cases (Registration of FIR / Zero FIR / e-FIR)",
        "historical_act": "CrPC",
        "historical_section": "154",
        "bailable": "Procedural",
        "cognizable": "Procedural",
        "court_trial": "Police Station / Jurisdictional Magistrate",
        "quantum": "Mandatory FIR registration"
    },
    "CrPC 164": {
        "modern_act": "BNSS",
        "modern_section": "183",
        "offense": "Recording of confessions and statements before Magistrate",
        "historical_act": "CrPC",
        "historical_section": "164",
        "bailable": "Procedural",
        "cognizable": "Procedural",
        "court_trial": "Judicial Magistrate",
        "quantum": "Evidentiary judicial record"
    },

    # Evidence Act -> BSA (Bharatiya Sakshya Adhiniyam 2023)
    "IEA 27": {
        "modern_act": "BSA",
        "modern_section": "23",
        "offense": "How much of information received from accused may be proved (Discovery of Fact)",
        "historical_act": "IEA",
        "historical_section": "27",
        "bailable": "Evidentiary Rule",
        "cognizable": "Evidentiary",
        "court_trial": "Trial Court",
        "quantum": "Admissibility of recovery of weapon/object"
    },
    "IEA 65B": {
        "modern_act": "BSA",
        "modern_section": "63",
        "offense": "Admissibility of electronic records and certificate requirement",
        "historical_act": "IEA",
        "historical_section": "65B",
        "bailable": "Evidentiary Rule",
        "cognizable": "Evidentiary",
        "court_trial": "All Courts",
        "quantum": "Electronic evidence certification"
    }
}


class StatutoryMapper:
    """Provides fast bidirectional mapping and text extraction of legal sections."""

    def __init__(self):
        self.mapping = STATUTORY_MAP
        self.reverse_map = {}
        for key, val in self.mapping.items():
            rev_key = f"{val['modern_act']} {val['modern_section']}"
            self.reverse_map[rev_key] = val

    def extract_sections(self, text: str) -> List[Dict[str, Any]]:
        """Extract statutory references from factual descriptions or petitions."""
        detected = []
        clean_text = text.upper()

        # Match IPC sections
        ipc_matches = re.findall(r'(?:SECTION|SEC\.?|S\.)?\s*([0-9]{1,3}[A-Z]?)\s*(?:OF\s+)?(?:THE\s+)?(?:IPC|INDIAN\s+PENAL\s+CODE)', clean_text)
        for sec in ipc_matches:
            key = f"IPC {sec}"
            if key in self.mapping:
                detected.append(self.mapping[key])

        # Match generic 302, 307, 420 mention if context has murder/cheating
        if "IPC 302" not in [d.get("historical_act") + " " + d.get("historical_section") for d in detected]:
            if re.search(r'\b(302|MURDER)\b', clean_text):
                detected.append(self.mapping["IPC 302"])
        if "IPC 420" not in [d.get("historical_act") + " " + d.get("historical_section") for d in detected]:
            if re.search(r'\b(420|CHEATING|FRAUD)\b', clean_text):
                detected.append(self.mapping["IPC 420"])
        if "CrPC 482" not in [d.get("historical_act") + " " + d.get("historical_section") for d in detected]:
            if re.search(r'\b(482|QUASH|QUASHING)\b', clean_text):
                detected.append(self.mapping["CrPC 482"])
        if "CrPC 439" not in [d.get("historical_act") + " " + d.get("historical_section") for d in detected]:
            if re.search(r'\b(439|BAIL|REGULAR BAIL)\b', clean_text) and not re.search(r'\b(ANTICIPATORY)\b', clean_text):
                detected.append(self.mapping["CrPC 439"])
        if "CrPC 438" not in [d.get("historical_act") + " " + d.get("historical_section") for d in detected]:
            if re.search(r'\b(438|ANTICIPATORY BAIL)\b', clean_text):
                detected.append(self.mapping["CrPC 438"])

        # Deduplicate
        seen = set()
        unique_results = []
        for item in detected:
            ident = f"{item['historical_act']} {item['historical_section']}"
            if ident not in seen:
                seen.add(ident)
                unique_results.append(item)

        return unique_results

    def get_details(self, section_str: str) -> Optional[Dict[str, Any]]:
        """Look up by IPC 302, BNS 103, CrPC 482, BNSS 483, etc. (case-insensitive)."""
        raw = section_str.strip()
        # Try direct match first
        if raw in self.mapping:
            return self.mapping[raw]
        # Try uppercase
        upper = raw.upper()
        if upper in self.mapping:
            return self.mapping[upper]
        # Try reverse map (modern act keys)
        if raw in self.reverse_map:
            return self.reverse_map[raw]
        if upper in self.reverse_map:
            return self.reverse_map[upper]
        # Case-insensitive scan over all keys
        raw_lower = raw.lower()
        for k, v in self.mapping.items():
            if k.lower() == raw_lower:
                return v
        for k, v in self.reverse_map.items():
            if k.lower() == raw_lower:
                return v
        return None

    def get_all_statutes(self) -> List[Dict[str, Any]]:
        return list(self.mapping.values())


# Singleton instance
statutory_mapper = StatutoryMapper()
