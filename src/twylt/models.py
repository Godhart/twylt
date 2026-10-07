"""Reusable strict contract model, TWYLT 1.1.0."""
from pydantic import BaseModel, ConfigDict

class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
