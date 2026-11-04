from pydantic import BaseModel, ConfigDict, Field


class MouzaCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    union_id: int = Field(gt=0)


class MouzaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    union_id: int
