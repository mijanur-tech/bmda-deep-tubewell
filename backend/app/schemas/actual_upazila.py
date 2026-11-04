from pydantic import (
    BaseModel,
    ConfigDict,
)


class ActualUpazilaResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    name: str
    management_unit_id: int