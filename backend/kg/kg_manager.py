"""Knowledge Graph Manager."""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import networkx as nx

class KGManager:
    """Local Knowledge Graph manager."""

    def __init__(self, db_path: str = "data/kg.db"):
        self.db_path = db_path
        self.kg_graph = nx.DiGraph()
        self.init_db()

    def init_db(self):
        """Initialize database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Nodes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                label TEXT,
                type TEXT,
                properties JSON
            )
        ''')

        # Edges table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS edges (
                source TEXT,
                target TEXT,
                relation TEXT,
                confidence REAL,
                evidence TEXT,
                PRIMARY KEY (source, target, relation)
            )
        ''')

        conn.commit()
        conn.close()

    def add_node(self, node_id: str, label: str, node_type: str, properties: Dict = None):
        """Add node to KG."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        props = json.dumps(properties or {})
        cursor.execute(
            "INSERT OR REPLACE INTO nodes VALUES (?, ?, ?, ?)",
            (node_id, label, node_type, props)
        )
        conn.commit()
        conn.close()
        self.kg_graph.add_node(node_id, label=label, type=node_type)

    def add_edge(self, source: str, target: str, relation: str, confidence: float, evidence: str = ""):
        """Add edge to KG."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO edges VALUES (?, ?, ?, ?, ?)",
            (source, target, relation, confidence, evidence)
        )
        conn.commit()
        conn.close()
        self.kg_graph.add_edge(source, target, relation=relation, weight=confidence)

    def load_umls(self, concepts_file: str):
        """Load UMLS concepts."""
        try:
            with open(concepts_file) as f:
                concepts = json.load(f)
                for concept in concepts:
                    self.add_node(
                        concept["concept_id"],
                        concept["name"],
                        concept["type"]
                    )
            print(f"✅ Loaded {len(concepts)} UMLS concepts")
        except Exception as e:
            print(f"Error loading UMLS: {e}")

    def load_disgenet(self, associations_file: str):
        """Load DisGeNET associations."""
        try:
            with open(associations_file) as f:
                assocs = json.load(f)
                for assoc in assocs:
                    gene_id = f"gene_{assoc['gene']}"
                    disease_id = f"disease_{assoc['disease']}"
                    self.add_node(gene_id, assoc['gene'], 'gene')
                    self.add_node(disease_id, assoc['disease'], 'disease')
                    self.add_edge(gene_id, disease_id, 'associates_with', assoc['score'])
            print(f"✅ Loaded {len(assocs)} DisGeNET associations")
        except Exception as e:
            print(f"Error loading DisGeNET: {e}")

    def load_ctd(self, interactions_file: str):
        """Load CTD interactions."""
        try:
            with open(interactions_file) as f:
                interactions = json.load(f)
                for inter in interactions:
                    chem_id = f"chem_{inter['chemical']}"
                    gene_id = f"gene_{inter['gene']}"
                    disease_id = f"disease_{inter['disease']}"
                    self.add_node(chem_id, inter['chemical'], 'chemical')
                    self.add_node(gene_id, inter['gene'], 'gene')
                    self.add_node(disease_id, inter['disease'], 'disease')
                    self.add_edge(chem_id, gene_id, inter['interaction'], 0.85)
                    self.add_edge(gene_id, disease_id, 'causes', 0.80)
            print(f"✅ Loaded {len(interactions)} CTD interactions")
        except Exception as e:
            print(f"Error loading CTD: {e}")

    def search_node(self, query: str, limit: int = 10) -> List[Dict]:
        """Search nodes by name."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, label, type FROM nodes WHERE label LIKE ? LIMIT ?",
            (f"%{query}%", limit)
        )
        results = [{"id": row[0], "label": row[1], "type": row[2]} for row in cursor.fetchall()]
        conn.close()
        return results

    def get_subgraph(self, center_id: str, depth: int = 2) -> Dict:
        """Get subgraph around a node."""
        nodes = set()
        edges = []

        def traverse(node_id: str, current_depth: int):
            if current_depth > depth:
                return
            nodes.add(node_id)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT target, relation, confidence FROM edges WHERE source = ?", (node_id,))
            for target, relation, conf in cursor.fetchall():
                edges.append({"source": node_id, "target": target, "relation": relation, "weight": conf})
                traverse(target, current_depth + 1)
            conn.close()

        traverse(center_id, 0)
        return {"nodes": list(nodes), "edges": edges, "depth": depth}

    def get_evidence_path(self, source: str, target: str, max_length: int = 3) -> Optional[List]:
        """Find evidence path between nodes."""
        try:
            path = nx.shortest_path(self.kg_graph, source, target, weight=lambda u, v, d: 1 - d.get('weight', 0.5))
            return path if len(path) <= max_length + 1 else None
        except nx.NetworkXNoPath:
            return None


def setup_kg():
    """Setup knowledge graph."""
    kg = KGManager()
    kg.load_umls("data/processed/umls_concepts.json")
    kg.load_disgenet("data/processed/disgenet_associations.json")
    kg.load_ctd("data/processed/ctd_interactions.json")
    return kg


if __name__ == "__main__":
    kg = setup_kg()
    print("✅ Knowledge graph initialized")
