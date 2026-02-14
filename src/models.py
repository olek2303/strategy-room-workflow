from enum import Enum
from pydantic import BaseModel, Field

class DecisionType(str, Enum):
    PROCEED = "PROCEED"
    ABORT = "ABORT"
    REVISE = "REVISE"

class RedTeamReport(BaseModel):
    identified_risks: list[str] = Field(description="List of specific risks")
    severity_score: int = Field(ge=1, le=10, description="Risk severity from 1 to 10")
    critical_flaw: bool = Field(description="Is there a showstopper flaw?")

class StrategicDecision(BaseModel):
    reasoning: str = Field(description="Detailed explanation weighing pros and cons")
    final_verdict: DecisionType = Field(description="Discrete final decision")

class ComplianceReport(BaseModel):
    is_compliant: bool = Field(description="True if the decision is 100% legally safe.")
    violations: list[str] = Field(description="List of specific rules broken, empty if safe.")
    mandatory_changes: str = Field(description="What CEO must change to pass compliance.")