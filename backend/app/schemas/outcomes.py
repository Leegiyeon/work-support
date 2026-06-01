from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

OutcomeType = Literal["quantitative", "qualitative"]


class OutcomeBaseModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class ProjectOutcomeCreate(OutcomeBaseModel):
    title: str = Field(..., min_length=1, max_length=180)
    outcome_type: OutcomeType = "qualitative"
    before_state: str = ""
    after_state: str = ""
    metric_name: str = ""
    metric_value: Decimal | None = None
    metric_unit: str = ""
    evidence_work_log_ids: list[UUID] = Field(default_factory=list)
    evidence_document_ids: list[UUID] = Field(default_factory=list)
    resume_ready: bool = False

    @model_validator(mode="after")
    def validate_quantitative_value(self) -> "ProjectOutcomeCreate":
        if self.outcome_type == "quantitative" and self.metric_value is None:
            raise ValueError("quantitative outcomes require metric_value")
        return self


class ProjectOutcomeUpdate(OutcomeBaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=180)
    outcome_type: OutcomeType | None = None
    before_state: str | None = None
    after_state: str | None = None
    metric_name: str | None = None
    metric_value: Decimal | None = None
    metric_unit: str | None = None
    evidence_work_log_ids: list[UUID] | None = None
    evidence_document_ids: list[UUID] | None = None
    resume_ready: bool | None = None


class OutcomeEvidenceWorkLog(BaseModel):
    id: str
    title: str
    log_date: str


class ProjectOutcome(BaseModel):
    id: str
    project_id: str
    title: str
    outcome_type: OutcomeType
    before_state: str = ""
    after_state: str = ""
    metric_name: str = ""
    metric_value: str | None = None
    metric_unit: str = ""
    evidence_work_log_ids: list[str] = Field(default_factory=list)
    evidence_document_ids: list[str] = Field(default_factory=list)
    evidence_work_logs: list[OutcomeEvidenceWorkLog] = Field(default_factory=list)
    resume_ready: bool = False
    created_at: str
    updated_at: str
