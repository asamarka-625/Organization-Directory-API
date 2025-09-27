# Внешние зависимости
from typing import List
from pydantic import BaseModel, constr, conint


PHONE_PATTERN = r'^[0-9\-]+$'


class OrganizationResponse(BaseModel):
    id: conint(ge=1)
    name: constr(min_length=1, max_length=100, strip_whitespace=True)
    phone_numbers: List[constr(min_length=1, max_length=20, strip_whitespace=True, pattern=PHONE_PATTERN)]
    building: constr(min_length=1, max_length=255, strip_whitespace=True)
    activities: List[constr(min_length=1, max_length=100, strip_whitespace=True)]
    

class BuildingOrganizationResponse(BaseModel):
    id: conint(ge=1)
    address: constr(min_length=1, max_length=255, strip_whitespace=True)
    latitude: float
    longitude: float
    organizations: List[OrganizationResponse]
    

class ActivityOrganizationResponse(BaseModel):
    id: conint(ge=1)
    activity: constr(min_length=1, max_length=100, strip_whitespace=True)
    organizations: List[OrganizationResponse]
