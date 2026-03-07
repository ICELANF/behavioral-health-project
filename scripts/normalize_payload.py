from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import os

client = QdrantClient(host="qdrant", port=6333)
COLLECTION = "bhp_knowledge"

FILE_RULES = {
    "bfr_framework.md":         {"layer":"L1","domain":"base","scope":"platform","evidence_level":"T1","ttm_stages":["S0","S1","S2","S3","S4","S5","S6"]},
    "ttm_stages.md":            {"layer":"L1","domain":"base","scope":"platform","evidence_level":"T1","ttm_stages":["S0","S1","S2","S3","S4","S5","S6"]},
    "bpt6_dimensions.md":       {"layer":"L1","domain":"base","scope":"platform","evidence_level":"T1","ttm_stages":["S0","S1","S2","S3","S4","S5","S6"]},
    "crisis_protocol.md":       {"layer":"L1","domain":"base","scope":"platform","evidence_level":"T1","ttm_stages":["S0","S1","S2","S3","S4","S5","S6"]},
    "diabetes_dietary_guide.md":{"layer":"L2","domain":"metabolic","scope":"domain","evidence_level":"T1","ttm_stages":["S1","S2","S3"]},
    "KI-DM-ACLM-LIFESTYLE-CPG-2025.md":{"layer":"L2","domain":"metabolic","scope":"domain","evidence_level":"T2","ttm_stages":["S2","S3","S4"]},
    "KI-CGM-AACE-CONSENSUS-2024.md":    {"layer":"L2","domain":"metabolic","scope":"domain","evidence_level":"T2","ttm_stages":["S1","S2","S3"]},
    "KI-GUT-MICROBIOME-2024.md":        {"layer":"L2","domain":"metabolic","scope":"domain","evidence_level":"T2","ttm_stages":["S2","S3"]},
    "hyperuricemia_gout_dietary_guide.md":{"layer":"L2","domain":"metabolic","scope":"domain","evidence_level":"T1","ttm_stages":["S1","S2","S3"]},
    "KI-TCM-NEIJING-BH-CORE-2024.md":  {"layer":"L2","domain":"tcm","scope":"domain","evidence_level":"T1","ttm_stages":["S0","S1","S2","S3","S4","S5"]},
    "KI-TCM-CONSTITUTION-chapters1-6.md":{"layer":"L2","domain":"tcm","scope":"domain","evidence_level":"T2","ttm_stages":["S1","S2","S3"]},
    "KI-BCT-NCDS-CONSENSUS-2024.md":   {"layer":"L2","domain":"behavioral","scope":"domain","evidence_level":"T2","ttm_stages":["S1","S2","S3","S4"]},
    "KI-COACH-ICF-COMPETENCY-2024.md": {"layer":"L2","domain":"behavioral","scope":"domain","evidence_level":"T2","ttm_stages":["S2","S3","S4","S5"]},
    "KI-ADDIC-PSYCHOLOGY-SHEN-2024.md":{"layer":"L2","domain":"behavioral","scope":"domain","evidence_level":"T3","ttm_stages":["S0","S1","S2","S3"]},
}

def get_rules(fname):
    if fname in FILE_RULES:
        return FILE_RULES[fname]
    f = fname.lower()
    if "growth" in f or "hbr" in f or "satir" in f or "nlp" in f:
        return {"layer":"L2","domain":"growth","scope":"domain","evidence_level":"T3","ttm_stages":["S4","S5","S6"]}
    if "tcm" in f or "neijing" in f or "constitution" in f:
        return {"layer":"L2","domain":"tcm","scope":"domain","evidence_level":"T2","ttm_stages":["S1","S2","S3"]}
    if "psychology" in f or "bl0" in f:
        return {"layer":"L2","domain":"behavioral","scope":"domain","evidence_level":"T3","ttm_stages":["S2","S3","S4"]}
    if any(x in f for x in ["clinical","ki-dm","ki-cd","ki-cgm","ki-gut","dietary","glucose","diabetes","obesity","lipid","hyper"]):
        return {"layer":"L2","domain":"metabolic","scope":"domain","evidence_level":"T2","ttm_stages":["S1","S2","S3"]}
    if any(x in f for x in ["coach","bct","fogg","bcw","behavior","addic","neuro","learn","erick","phil","cult"]):
        return {"layer":"L2","domain":"behavioral","scope":"domain","evidence_level":"T3","ttm_stages":["S2","S3","S4"]}
    return {"layer":"L2","domain":"general","scope":"domain","evidence_level":"T3","ttm_stages":["S1","S2","S3"]}

offset = None
updated = 0
skipped = 0
batch = []

while True:
    res, offset = client.scroll(COLLECTION, offset=offset, limit=100, with_payload=True, with_vectors=True)
    for p in res:
        if p.payload.get("layer"):
            skipped += 1
            continue
        fname = p.payload.get("source_file", "")
        rules = get_rules(fname)
        batch.append(PointStruct(id=p.id, vector=p.vector, payload={**p.payload, **rules}))
        updated += 1
    if offset is None:
        break

for i in range(0, len(batch), 50):
    client.upsert(COLLECTION, points=batch[i:i+50])

print(f"更新: {updated}, 跳过: {skipped}")
