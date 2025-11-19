"""Annotation schema for Causal-NLP Engine."""

import json
from pathlib import Path

ANNOTATION_SCHEMA = {
    "version": "1.0",
    "labels": {
        "CAUSAL_VALID": {
            "description": "Causal link is scientifically valid with evidence",
            "color": "green",
            "icon": "✓"
        },
        "CAUSAL_INVALID": {
            "description": "Causal link contradicts established science",
            "color": "red",
            "icon": "✗"
        },
        "CORRELATION_NOT_CAUSAL": {
            "description": "Evidence shows correlation only, not causation",
            "color": "yellow",
            "icon": "~"
        },
        "UNVERIFIABLE": {
            "description": "Insufficient evidence to verify the claim",
            "color": "gray",
            "icon": "?"
        },
        "MISSING_MECHANISM": {
            "description": "Causal link plausible but mechanistic pathway unclear",
            "color": "blue",
            "icon": "→"
        }
    },
    "annotation_instructions": """
# Causal Claim Annotation Guidelines

## Task
Evaluate whether causal relationships in scientific claims are valid based on current evidence.

## Labels

### CAUSAL_VALID (✓ Green)
- Strong scientific evidence supports the causal claim
- Mechanistic pathway is well-established
- Multiple peer-reviewed studies confirm
Example: "Aspirin reduces pain through COX inhibition"

### CAUSAL_INVALID (✗ Red)
- Scientific evidence contradicts the claim
- Mechanistic pathway is implausible
- Study has been refuted or shown false
Example: "Drinking bleach cures COVID-19"

### CORRELATION_NOT_CAUSAL (~ Yellow)
- Evidence shows correlation, not causation
- May be confounded variables
- No clear mechanistic pathway
Example: "Red wine consumption correlates with health, therefore wine is healthy"

### UNVERIFIABLE (? Gray)
- No sufficient scientific evidence found
- Claim is too new or niche
- Limited research availability
Example: "New compound X treats disease Y" (unpublished)

### MISSING_MECHANISM (→ Blue)
- Causal link might be valid but mechanism unknown
- Needs further research
- Preliminary evidence exists
Example: "Meditation reduces anxiety" (mechanism not fully understood)

## Annotation Process
1. Read the scientific claim
2. Identify causal relationships (Subject → Relation → Object)
3. Search for supporting/contradicting evidence
4. Assess mechanistic plausibility
5. Select appropriate label
6. Add comments if needed

## Quality Checks
- Avoid personal opinions
- Base decisions on peer-reviewed research
- Consider publication date (prioritize recent)
- Check for conflicts of interest
- Document evidence sources
""",
    "sample_annotations": [
        {
            "claim_id": "001",
            "claim_text": "Turmeric consumption reduces inflammation",
            "label": "CORRELATION_NOT_CAUSAL",
            "confidence": 0.85,
            "reasoning": "Curcumin in turmeric has anti-inflammatory properties in vitro, but clinical evidence for whole turmeric consumption is weak and mixed.",
            "evidence_pmids": ["12345678", "87654321"],
            "annotator": "expert_001",
            "date": "2025-01-15"
        },
        {
            "claim_id": "002",
            "claim_text": "Aspirin inhibits platelet aggregation",
            "label": "CAUSAL_VALID",
            "confidence": 0.98,
            "reasoning": "Well-established mechanism: aspirin acetylates COX-1 → blocks TXA2 production → inhibits platelet aggregation. Hundreds of studies confirm.",
            "evidence_pmids": ["111111", "222222"],
            "annotator": "expert_002",
            "date": "2025-01-15"
        }
    ]
}


def save_annotation_schema():
    """Save annotation schema."""
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    
    # Save JSON schema
    schema_path = docs_dir / "annotation_schema.json"
    with open(schema_path, 'w') as f:
        json.dump(ANNOTATION_SCHEMA, f, indent=2)
    
    # Save markdown guide
    md_path = docs_dir / "annotation_guide.md"
    with open(md_path, 'w') as f:
        f.write(ANNOTATION_SCHEMA["annotation_instructions"])
    
    print(f"✅ Saved annotation schema to {schema_path}")
    print(f"✅ Saved annotation guide to {md_path}")


def generate_label_studio_config():
    """Generate Label Studio XML configuration."""
    xml_config = """<View>
  <Text name="text" value="$text"/>
  <Choices name="label" toName="text" choice="single" required="true">
    <Choice value="CAUSAL_VALID" background="green"/>
    <Choice value="CAUSAL_INVALID" background="red"/>
    <Choice value="CORRELATION_NOT_CAUSAL" background="yellow"/>
    <Choice value="UNVERIFIABLE" background="gray"/>
    <Choice value="MISSING_MECHANISM" background="blue"/>
  </Choices>
  <TextArea name="reasoning" toName="text" placeholder="Explain your annotation" />
  <TextArea name="evidence" toName="text" placeholder="List evidence (PMIDs)" />
</View>"""
    
    config_path = Path("docs/label_studio_config.xml")
    with open(config_path, 'w') as f:
        f.write(xml_config)
    
    print(f"✅ Saved Label Studio config to {config_path}")


if __name__ == "__main__":
    save_annotation_schema()
    generate_label_studio_config()
