from pydantic import BaseModel


class EventSchema(BaseModel):
    method: str
    event: dict
    timestamp: str
