# Внешние зависимости
from typing import List, Optional, Union
from fastapi import APIRouter, HTTPException, status
from pydantic import constr, conint
# Внутренние модули
from app.schemas import OrganizationResponse, BuildingOrganizationResponse, ActivityOrganizationResponse
from app.crud import (sql_get_organizations_by_building_id, sql_get_organizations_by_activity_id,
                      sql_get_buildings_and_organizations_by_raduis, sql_get_organization_by_id,
                      sql_get_organizations_by_activity_with_nested, sql_get_organization_by_name)


router = APIRouter(
    prefix="/api/v1",
    tags=["Organizations - Организации"],
    responses={
        400: {"description": "Неверный запрос"},
        404: {"description": "Организация не найдена"},
        500: {"description": "Внутренняя ошибка сервера"}
    }
)


# Выводим организацию по идентификатору
@router.get(
    "/organizations/{id_organization}",
    response_model=OrganizationResponse,
    summary="Получить организацию по ID",
    description="""
    Возвращает полную информацию об организации по её идентификатору.
    
    **Требования:**
    - ID организации должен быть целым числом ≥ 1
    """
)
async def get_organization_by_id(id_organization: conint(ge=1)):
    result = await sql_get_organization_by_id(id_organization=id_organization)
    
    return result
    
    
# Выводим организации по параметрам
@router.get(
    "/organizations/",
    response_model=Union[
        List[OrganizationResponse], List[BuildingOrganizationResponse],
        OrganizationResponse, BuildingOrganizationResponse, ActivityOrganizationResponse
    ],
    summary="Поиск организаций по параметрам",
    description="""
    Гибкий поиск организаций по различным критериям. 
    Поддерживает несколько режимов поиска в зависимости от переданных параметров.
    
    **Режимы поиска:**
    - По ID здания (`building_id`)
    - По ID вида деятельности (`activity_id`) 
    - По названию вида деятельности (`activity_name`)
    - По названию организации (`name_organization`)
    - По географическому радиусу (`latitude`, `longitude`, `radius`)
    
    **Важно:** Используется только один параметр за раз. Приоритет параметров сверху вниз.
    """
)
async def get_organizations(
    building_id: Optional[conint(ge=1)] = None,
    activity_id: Optional[conint(ge=1)] = None,
    activity_name: Optional[constr(min_length=1, max_length=100, strip_whitespace=True)] = None,
    name_organization: Optional[constr(min_length=1, max_length=100, strip_whitespace=True)] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius: Optional[float] = None,
):
    if building_id is not None:
        result = await sql_get_organizations_by_building_id(building_id=building_id)
    
    elif activity_id is not None:
        result = await sql_get_organizations_by_activity_id(activity_id=activity_id)
        
    elif activity_name is not None:
        result = await sql_get_organizations_by_activity_with_nested(activity_name=activity_name)
    
    elif name_organization is not None:
        result = await sql_get_organization_by_name(name_organization=name_organization)
        
    elif latitude is not None and longitude is not None and radius is not None:
        result = await sql_get_buildings_and_organizations_by_raduis(lat=latitude, lon=longitude, radius=radius)
    
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")
        
    return result

    
   