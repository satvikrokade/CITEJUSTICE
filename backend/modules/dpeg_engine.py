"""
Dynamic Precedent Evolution Graph (DPEG) Engine for CiteJustice
Implements the flagship DPEG Authority scoring formula:
Authority = 2F + R - D - 3O
where:
  F = Followed count
  R = Relied Upon count
  D = Distinguished count
  O = Overruled count
Suppresses dead law and elevates currently valid legal precedents.
"""

import networkx as nx
from typing import Dict, List, Any, Optional, Tuple


class DPEGEngine:
    """Manages the citation graph, computes DPEG authority scores, and projects subgraphs."""

    def __init__(self):
        self.graph = nx.DiGraph()
        self._initialize_benchmark_graph()

    def add_precedent_case(
        self,
        case_id: str,
        title: str,
        citation: str,
        court: str = "Supreme Court of India",
        year: int = 2024,
        bench_strength: int = 2,
        status: str = "ACTIVE",
        statutory_sections: List[str] = None,
        ratio_decidendi: str = "",
        key_facts: str = "",
        raw_html: str = ""
    ):
        """Add a legal judgment node into the precedent graph."""
        self.graph.add_node(
            case_id,
            case_id=case_id,
            title=title,
            citation=citation,
            court=court,
            year=year,
            bench_strength=bench_strength,
            status=status,
            statutory_sections=statutory_sections or [],
            ratio_decidendi=ratio_decidendi,
            key_facts=key_facts,
            raw_html=raw_html
        )

    def add_citation_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,  # FOLLOWED, RELIED_UPON, DISTINGUISHED, OVERRULED, AFFIRMED
        year: int,
        court: str = "Supreme Court of India",
        notes: str = ""
    ):
        """Add a directed legal citation relationship: source_id treats target_id as rel_type."""
        rel_type_upper = rel_type.upper()
        self.graph.add_edge(
            source_id,
            target_id,
            rel_type=rel_type_upper,
            year=year,
            court=court,
            notes=notes
        )

    def calculate_authority_score(self, case_id: str) -> Dict[str, Any]:
        """
        Computes the DPEG Authority Score:
        Authority = 2F + R - D - 3O
        Also checks if the case was explicitly overruled by any subsequent judgment.
        """
        if case_id not in self.graph:
            return {"authority": 0, "F": 0, "R": 0, "D": 0, "O": 0, "is_overruled": False, "status": "UNKNOWN"}

        # Incoming edges: subsequent cases pointing to this case
        in_edges = self.graph.in_edges(case_id, data=True)
        
        f_count = 0
        r_count = 0
        d_count = 0
        o_count = 0
        overruled_by = []

        for src, _, data in in_edges:
            rel = data.get("rel_type", "")
            if rel == "FOLLOWED":
                f_count += 1
            elif rel in ("RELIED_UPON", "RELIED"):
                r_count += 1
            elif rel == "DISTINGUISHED":
                d_count += 1
            elif rel == "OVERRULED":
                o_count += 1
                src_node = self.graph.nodes.get(src, {})
                overruled_by.append({
                    "case_id": src,
                    "title": src_node.get("title", src),
                    "citation": src_node.get("citation", ""),
                    "year": data.get("year", 0)
                })

        # Calculate exact formula
        raw_authority = (2 * f_count) + (1 * r_count) - (1 * d_count) - (3 * o_count)
        is_overruled = (o_count > 0)

        status = "ACTIVE"
        if is_overruled:
            status = "OVERRULED"
        elif d_count > f_count + r_count:
            status = "RESTRICTED"
        elif f_count + r_count > 2:
            status = "SETTLED_LAW"

        return {
            "case_id": case_id,
            "authority_score": raw_authority,
            "F": f_count,
            "R": r_count,
            "D": d_count,
            "O": o_count,
            "is_overruled": is_overruled,
            "overruled_by": overruled_by,
            "status": status
        }

    def get_subgraph_for_cases(self, case_ids: List[str], hops: int = 1) -> Dict[str, Any]:
        """Extract a self-contained sub-graph of nodes and links suitable for WebGL 3D/2D visualization."""
        target_nodes = set(case_ids)
        expanded_nodes = set(target_nodes)

        for _ in range(hops):
            current = list(expanded_nodes)
            for node in current:
                if node in self.graph:
                    expanded_nodes.update(self.graph.predecessors(node))
                    expanded_nodes.update(self.graph.successors(node))

        nodes_data = []
        links_data = []

        for node_id in expanded_nodes:
            if node_id in self.graph:
                node_attr = dict(self.graph.nodes[node_id])
                auth_info = self.calculate_authority_score(node_id)
                node_attr.update(auth_info)
                node_attr["id"] = node_id
                nodes_data.append(node_attr)

        for u, v, data in self.graph.edges(data=True):
            if u in expanded_nodes and v in expanded_nodes:
                links_data.append({
                    "source": u,
                    "target": v,
                    "rel_type": data.get("rel_type", "CITES"),
                    "year": data.get("year", ""),
                    "notes": data.get("notes", "")
                })

        return {
            "nodes": nodes_data,
            "links": links_data,
            "summary": {
                "total_nodes": len(nodes_data),
                "total_links": len(links_data)
            }
        }

    def _initialize_benchmark_graph(self):
        """
        Populate the graph with benchmark precedent chains including the Murder/IPC 302
        evolution from the project synopsis & research papers, plus constitutional & bail precedents.
        """
        # --- Precedent Chain 1: Murder (IPC 302 / BNS 103) & Mens Rea Evolution ---
        # Case A: Historical baseline on sudden provocation vs premeditation
        self.add_precedent_case(
            case_id="SC-1976-A",
            title="State of Maharashtra v. Digambar Shankar & Ors.",
            citation="1976 AIR SC 123",
            court="Supreme Court of India",
            year=1976,
            bench_strength=2,
            status="OVERRULED",
            statutory_sections=["IPC 302", "IPC 304", "BNS 103"],
            ratio_decidendi="Single fatal blow with sharp weapon automatically infers murder without examining grave provocation.",
            key_facts="Accused used a sharp agricultural tool following a heated village boundary altercation causing instantaneous death."
        )

        # Case B: Followed Case A initially
        self.add_precedent_case(
            case_id="SC-1985-B",
            title="Kishan Lal v. State of Rajasthan",
            citation="1985 (3) SCC 412",
            court="Supreme Court of India",
            year=1985,
            bench_strength=2,
            status="RESTRICTED",
            statutory_sections=["IPC 302", "BNS 103"],
            ratio_decidendi="Applied strict single fatal blow test holding knowledge and intention co-extensive.",
            key_facts="Fight broke out during water sharing; accused struck victim on temple with heavy iron rod."
        )

        # Case C: Distinguished Case B on lack of premeditation
        self.add_precedent_case(
            case_id="SC-2008-C",
            title="Gurmail Singh & Anr. v. State of Punjab",
            citation="2008 (14) SCC 510",
            court="Supreme Court of India",
            year=2008,
            bench_strength=3,
            status="ACTIVE",
            statutory_sections=["IPC 300", "IPC 304 Part I", "BNS 105"],
            ratio_decidendi="Exception 4 to Section 300 applies where sudden fight ensues without premeditation and offender did not take undue advantage.",
            key_facts="Sudden quarrel occurred without weapons premeditated; converted conviction from Section 302 to Section 304 Part I."
        )

        # Case D: Constitution Bench overruling Case A directly
        self.add_precedent_case(
            case_id="SC-2016-D",
            title="Sunder Singh v. State of Uttarakhand (Constitution Bench)",
            citation="2016 (9) SCC 801",
            court="Supreme Court of India",
            year=2016,
            bench_strength=5,
            status="ACTIVE",
            statutory_sections=["IPC 300", "IPC 302", "IPC 304", "BNS 103", "BNS 105"],
            ratio_decidendi="Explicitly overruled Digambar Shankar (1976). Bodily injury alone cannot dispense with proving subjective intention under Section 300 Clause 3.",
            key_facts="Five-judge bench resolved conflicting High Court rulings regarding single blow injuries in sudden fights."
        )

        # Case E: Modern landmark affirming Exception 4 & BNS equivalence
        self.add_precedent_case(
            case_id="SC-2023-E",
            title="Anbazhagan v. The State represented by Inspector of Police",
            citation="2023 INSC 644",
            court="Supreme Court of India",
            year=2023,
            bench_strength=3,
            status="ACTIVE",
            statutory_sections=["IPC 302", "IPC 304", "BNS 103", "BNS 105"],
            ratio_decidendi="Exhaustive guidelines categorizing culpable homicide vs murder. Held that absence of prior enmity and sudden mutual fight warrants Section 304 Part II.",
            key_facts="Altercation during festival leading to single stab wound. Supreme Court laid down 10-point test."
        )

        # Setup Causal Citation Links for Chain 1
        self.add_citation_relationship("SC-1985-B", "SC-1976-A", "FOLLOWED", 1985, notes="Followed single fatal blow doctrine")
        self.add_citation_relationship("SC-2008-C", "SC-1985-B", "DISTINGUISHED", 2008, notes="Distinguished on facts of sudden quarrel and lack of premeditation")
        self.add_citation_relationship("SC-2016-D", "SC-1976-A", "OVERRULED", 2016, notes="Overruled Digambar Shankar as bad law")
        self.add_citation_relationship("SC-2023-E", "SC-2008-C", "FOLLOWED", 2023, notes="Affirmed Gurmail Singh Exception 4 doctrine")
        self.add_citation_relationship("SC-2023-E", "SC-2016-D", "RELIED_UPON", 2023, notes="Adopted 5-judge intention test")

        # --- Precedent Chain 2: Bail & Liberty (CrPC 438/439 / BNSS 482/483) ---
        self.add_precedent_case(
            case_id="SC-2014-ARNESH",
            title="Arnesh Kumar v. State of Bihar & Anr.",
            citation="(2014) 8 SCC 273",
            court="Supreme Court of India",
            year=2014,
            bench_strength=2,
            status="ACTIVE",
            statutory_sections=["CrPC 41", "CrPC 439", "IPC 498A", "BNSS 35", "BNS 85"],
            ratio_decidendi="Mandated notice under Section 41A CrPC before arrest in offenses punishable with imprisonment up to 7 years. Arrest should not be mechanical.",
            key_facts="Harassment case under 498A IPC where indiscriminate arrest was made without recording reasons."
        )

        self.add_precedent_case(
            case_id="SC-2020-GURBAKSH",
            title="Sushila Aggarwal & Ors. v. State (NCT of Delhi) (5-Judge Bench)",
            citation="(2020) 5 SCC 1",
            court="Supreme Court of India",
            year=2020,
            bench_strength=5,
            status="ACTIVE",
            statutory_sections=["CrPC 438", "BNSS 482"],
            ratio_decidendi="Anticipatory bail under Section 438 should not invariably be limited to a fixed time frame. Protection normally continues till the end of the trial.",
            key_facts="Constitution bench settled 40 years of jurisprudence on pre-arrest bail duration."
        )

        self.add_precedent_case(
            case_id="SC-2022-SATENDER",
            title="Satender Kumar Antil v. Central Bureau of Investigation",
            citation="(2022) 10 SCC 51",
            court="Supreme Court of India",
            year=2022,
            bench_strength=2,
            status="ACTIVE",
            statutory_sections=["CrPC 437", "CrPC 439", "BNSS 480", "BNSS 483"],
            ratio_decidendi="Categorized offenses into 4 categories (A, B, C, D) for grant of bail without police remand. Reaffirmed bail is the rule and jail is the exception.",
            key_facts="Comprehensive directions to trial courts to avoid unnecessary custody."
        )

        self.add_citation_relationship("SC-2022-SATENDER", "SC-2014-ARNESH", "FOLLOWED", 2022, notes="Mandated trial court compliance with Arnesh Kumar guidelines")
        self.add_citation_relationship("SC-2022-SATENDER", "SC-2020-GURBAKSH", "RELIED_UPON", 2022, notes="Reiterated constitutional liberty tenets")

        # --- Precedent Chain 3: Quashing under Inherent Powers (CrPC 482 / BNSS 528) ---
        self.add_precedent_case(
            case_id="SC-1992-BHAJAN",
            title="State of Haryana & Ors. v. Bhajan Lal & Ors.",
            citation="1992 Supp (1) SCC 335",
            court="Supreme Court of India",
            year=1992,
            bench_strength=2,
            status="ACTIVE",
            statutory_sections=["CrPC 482", "BNSS 528"],
            ratio_decidendi="Laid down 7 landmark parameters where High Court must exercise inherent power under Section 482 to quash FIR to prevent abuse of process.",
            key_facts="Allegations of corruption where uncontroverted FIR allegations did not disclose cognizable offense."
        )

        self.add_precedent_case(
            case_id="SC-2021-NEEHARIKA",
            title="Neeharika Infrastructure Pvt. Ltd. v. State of Maharashtra",
            citation="2021 SCC OnLine SC 315",
            court="Supreme Court of India",
            year=2021,
            bench_strength=3,
            status="ACTIVE",
            statutory_sections=["CrPC 482", "BNSS 528"],
            ratio_decidendi="High Courts should not pass blanket orders of 'no coercive steps' or stay of investigation while entertaining petitions under Section 482.",
            key_facts="Commercial dispute where High Court stayed police probe without recording reasons."
        )

        self.add_citation_relationship("SC-2021-NEEHARIKA", "SC-1992-BHAJAN", "DISTINGUISHED", 2021, notes="Restricted Bhajan Lal category 7 to prevent premature interference with statutory police investigation")


# Singleton instance
dpeg_engine = DPEGEngine()
