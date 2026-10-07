"""Modelos de datos para emisión de pólizas y transactional outbox."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class PolicyIssueRequest(BaseModel):
    quote_id: str
    tier: str
    insured_document: str
    beneficiaries: List[dict] = Field(default_factory=list)


class PolicyRecord(BaseModel):
    policy_number: str
    quote_id: str
    status: str = Field(default="ISSUED")
    issued_at: str
    pdf_s3_key: str
    outbox_event_id: str
