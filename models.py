from pydantic import BaseModel, Field
from typing import List


class BomItem(BaseModel):
    code: str
    item: str
    quantity: float
    cost_bdt: float


class AssessmentRecord(BaseModel):
    report_hash: str
    created_at: str
    gps: str
    exif_verified: bool
    infra_type: str
    est_span: float
    status: str
    damage_type: str
    ai_severity: str
    structural_notes: str
    confidence: float = Field(ge=0.0, le=1.0)
    final_severity: str
    bom: List[BomItem]
    total_cost: float
    repair_time: str
