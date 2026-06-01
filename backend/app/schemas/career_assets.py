from pydantic import BaseModel


class CareerAsset(BaseModel):
    id: str
    project_id: str
    source_summary: str = ""
    work_summary: str = ""
    outcome_summary: str = ""
    resume_bullets: str = ""
    career_description: str = ""
    portfolio_description: str = ""
    star_answer: str = ""
    markdown: str = ""
    generation_method: str = "template"
    created_at: str
    updated_at: str
