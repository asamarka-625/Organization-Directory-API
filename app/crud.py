# Внешние зависимости
from typing import List
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from fastapi import HTTPException, status
# Внутренние модули
from app.config import get_config
from app.models import Building, Organization, Activity, organization_activity
from app.database import connection
from app.schemas import OrganizationResponse, BuildingOrganizationResponse, ActivityOrganizationResponse


config = get_config()


# Получаем организации по идентификатору здания
@connection
async def sql_get_organizations_by_building_id(building_id: int, session: AsyncSession) -> BuildingOrganizationResponse:
    try:
        building_result = await session.execute(
            sa.select(Building)
            .where(Building.id == building_id)
            .options(
                so.selectinload(Building.connect_organization).selectinload(Organization.connect_activities),
                so.selectinload(Building.connect_organization).selectinload(Organization.connect_numbers)
            )
        )
        building = building_result.scalar_one()
        
        return BuildingOrganizationResponse(
            id=building.id,
            address=building.address,
            latitude=building.latitude,
            longitude=building.longitude,
            organizations=[
                OrganizationResponse(
                    id=org.id,
                    name=org.name,
                    phone_numbers=[phone.number for phone in org.connect_numbers],
                    building=building.address,
                    activities=[activity.name for activity in org.connect_activities]
                )
                for org in building.connect_organization
            ]
        )
        
    except NoResultFound:
        config.logger.info(f"Building not found by building_id {building_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found")
        
    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading building by building_id {building_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
        
    except Exception as e:
        config.logger.error(f"Unexpected error reading building by building_id {building_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")
        

# Получаем организации по идентификатору деятельности
@connection
async def sql_get_organizations_by_activity_id(activity_id: int, session: AsyncSession) -> ActivityOrganizationResponse:
    try:
        activity_result = await session.execute(
            sa.select(Activity)
            .where(Activity.id == activity_id)
            .options(
                so.selectinload(Activity.connect_organizations).selectinload(Organization.connect_building),
                so.selectinload(Activity.connect_organizations).selectinload(Organization.connect_numbers),
                so.selectinload(Activity.connect_organizations).selectinload(Organization.connect_activities)
            )
        )
        activity = activity_result.scalar_one()
        
        return ActivityOrganizationResponse(
            id=activity.id,
            activity=activity.name,
            organizations=[
                OrganizationResponse(
                    id=org.id,
                    name=org.name,
                    phone_numbers=[phone.number for phone in org.connect_numbers],
                    building=org.connect_building.address,
                    activities=[activity.name for activity in org.connect_activities]
                )
                for org in activity.connect_organizations
            ]
        )
        
    except NoResultFound:
        config.logger.info(f"Activity not found by activity_id {activity_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
        
    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading activity by activity_id {activity_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
        
    except Exception as e:
        config.logger.error(f"Unexpected error reading activity by activity_id {activity_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")
        

# Получаем организации, которые находятся в заданном радиусе
@connection
async def sql_get_buildings_and_organizations_by_raduis(
    lat: float,
    lon: float,
    radius: float,
    session: AsyncSession
) -> List[BuildingOrganizationResponse]:
    try:
        buildings_result = await session.execute(
            sa.select(Building)
            .where(
                6371 * 2 * sa.func.asin(
                    sa.func.sqrt(
                        sa.func.pow(sa.func.sin((sa.func.radians(lat) - sa.func.radians(Building.latitude)) / 2), 2) +
                        sa.func.cos(sa.func.radians(lat)) * 
                        sa.func.cos(sa.func.radians(Building.latitude)) * 
                        sa.func.pow(sa.func.sin((sa.func.radians(lon) - sa.func.radians(Building.longitude)) / 2), 2)
                    )
                ) <= radius
            )
            .options(
                so.selectinload(Building.connect_organization).selectinload(Organization.connect_activities),
                so.selectinload(Building.connect_organization).selectinload(Organization.connect_numbers)
            )
        )
        
        buildings = buildings_result.scalars().all()
        
        if not buildings:
            raise NoResultFound
        
        return [
            BuildingOrganizationResponse(
                id=building.id,
                address=building.address,
                latitude=building.latitude,
                longitude=building.longitude,
                organizations=[
                    OrganizationResponse(
                        id=org.id,
                        name=org.name,
                        phone_numbers=[phone.number for phone in org.connect_numbers],
                        building=building.address,
                        activities=[activity.name for activity in org.connect_activities]
                    )
                    for org in building.connect_organization
                ]
            )
            for building in buildings
        ]
        
    except NoResultFound:
        config.logger.info(f"Buildings not found by latitude: {lat}, longitude: {lon}, radius: {radius}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buildings not found")
        
    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading buildings by latitude: {lat}, longitude: {lon}, radius: {radius} - {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
        
    except Exception as e:
        config.logger.error(f"Unexpected error reading buildings by latitude: {lat}, longitude: {lon}, radius: {radius} - {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")
    

# Получаем организацию по идентификатору
@connection
async def sql_get_organization_by_id(id_organization: int, session: AsyncSession) -> OrganizationResponse:
    try:
        organization_result = await session.execute(
            sa.select(Organization)
            .where(Organization.id == id_organization)
            .options(
                so.joinedload(Organization.connect_building),
                so.selectinload(Organization.connect_activities),
                so.selectinload(Organization.connect_numbers)
            )
        )
        organization = organization_result.scalar_one()
            
        return OrganizationResponse(
            id=organization.id,
            name=organization.name,
            phone_numbers=[phone.number for phone in organization.connect_numbers],
            building=organization.connect_building.address,
            activities=[activity.name for activity in organization.connect_activities]
        )
        
    except NoResultFound:
        config.logger.info(f"Organization not found by id_organization: {id_organization}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
        
    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading organization by id_organization: {id_organization}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
        
    except Exception as e:
        config.logger.error(f"Unexpected error reading organization by id_organization: {id_organization}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")
        

# Получаем организации по виду деятельности со вложениями
@connection
async def sql_get_organizations_by_activity_with_nested(activity_name: str, session: AsyncSession) -> List[OrganizationResponse]:
    try:
        root_activity_id_result = await session.execute(
            sa.select(Activity.id)
            .where(Activity.name == activity_name)
        )
        root_activity_id = root_activity_id_result.scalar_one()
        
        activities_cte = (
            sa.select(Activity.id, sa.literal(0).label('level'))
            .where(Activity.id == root_activity_id)
            .cte(name="activities_cte", recursive=True)
        )
        
        activities_recursive = sa.select(
            Activity.id,
            (activities_cte.c.level + 1).label('level')
        ).where(
            sa.and_(
                Activity.parent_id == activities_cte.c.id,
                activities_cte.c.level < 2
            )
        )
        
        activities_cte = activities_cte.union_all(activities_recursive)
        
        organizations_result = await session.execute(
            sa.select(Organization)
            .join(organization_activity, Organization.id == organization_activity.c.organization_id)
            .where(organization_activity.c.activity_id.in_(sa.select(activities_cte.c.id)))
            .options(
                so.joinedload(Organization.connect_building),
                so.selectinload(Organization.connect_activities),
                so.selectinload(Organization.connect_numbers)
            )
            .distinct()
        )
        
        return [
            OrganizationResponse(
                id=org.id,
                name=org.name,
                phone_numbers=[phone.number for phone in org.connect_numbers],
                building=org.connect_building.address,
                activities=[activity.name for activity in org.connect_activities]
            )
            for org in organizations_result.scalars().all()
        ]
        
    except NoResultFound:
        config.logger.info(f"Activity not found by activity name: {activity_name}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
        
    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading activity by activity name: {activity_name}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
        
    except Exception as e:
        config.logger.error(f"Unexpected error reading activity by activity name: {activity_name}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")
        
        
# Получаем организацию по названию
@connection
async def sql_get_organization_by_name(name_organization: str, session: AsyncSession) -> OrganizationResponse:
    try:
        organization_result = await session.execute(
            sa.select(Organization)
            .where(Organization.name == name_organization)
            .options(
                so.joinedload(Organization.connect_building),
                so.selectinload(Organization.connect_activities),
                so.selectinload(Organization.connect_numbers)
            )
        )
        organization = organization_result.scalar_one()
            
        return OrganizationResponse(
            id=organization.id,
            name=organization.name,
            phone_numbers=[phone.number for phone in organization.connect_numbers],
            building=organization.connect_building.address,
            activities=[activity.name for activity in organization.connect_activities]
        )
        
    except NoResultFound:
        config.logger.info(f"Organization not found by name_organization: {name_organization}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
        
    except SQLAlchemyError as e:
        config.logger.error(f"Database error reading organization by name_organization: {name_organization}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
        
    except Exception as e:
        config.logger.error(f"Unexpected error reading organization by name_organization: {name_organization}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")