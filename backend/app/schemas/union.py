from pydantic import BaseModel, ConfigDict, Field


class UnionCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    actual_upazila_id: int = Field(gt=0)


class UnionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    actual_upazila_id: int
