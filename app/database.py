# Внешние зависимости
from typing import List
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import sqlalchemy as sa
# Внутренние модули
from app.config import get_config
from app.models import Base, Building, Organization, Activity, PhoneNumber, organization_activity


# Получаем конфиг
config = get_config()

engine = create_async_engine(config.DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


# Инициализируем таблицы
async def setup_database():
    config.logger.info(f"Инициализируем таблицы")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
            

# Декоратор подключения к базе данных         
def connection(method):
    async def wrapper(*args, **kwargs):
        if kwargs.pop('no_decor', False):
            return await method(*args, **kwargs)
            
        async with AsyncSessionLocal() as session:
            try:
                return await method(*args, session=session, **kwargs)
                
            except Exception as e:
                await session.rollback() 
                raise e
                
            finally:
                await session.close()
    
    return wrapper
    

# Рекурсивно создает иерархию активностей
async def create_activity_hierarchy(data, session, parent=None) -> List[int]:
    activity = Activity(name=data["name"], parent=parent)
    session.add(activity)
    await session.flush()
    
    activities = []
    activities.append(activity.id)
    
    for child_data in data.get("children", []):
        childs_activity = await create_activity_hierarchy(data=child_data, parent=activity, session=session)
        activities.extend(childs_activity)
        
    return activities

        
# Заполнение тестовыми данными
@connection  
async def seed_database(session: AsyncSession):
    try:
        config.logger.info("Очищаем таблицы")
        
        # Удаляем данные из таблиц
        await session.execute(sa.text("DELETE FROM phone_numbers"))
        await session.execute(sa.text("DELETE FROM organization_activity"))
        await session.execute(sa.text("DELETE FROM organizations"))
        await session.execute(sa.text("DELETE FROM activities"))
        await session.execute(sa.text("DELETE FROM buildings"))
        
        # Сбрасываем автоинкрементацию для каждой таблицы
        await session.execute(sa.text("ALTER SEQUENCE phone_numbers_id_seq RESTART WITH 1"))
        await session.execute(sa.text("ALTER SEQUENCE organizations_id_seq RESTART WITH 1"))
        await session.execute(sa.text("ALTER SEQUENCE activities_id_seq RESTART WITH 1"))
        await session.execute(sa.text("ALTER SEQUENCE buildings_id_seq RESTART WITH 1"))
        
        await session.commit()
        
        config.logger.info("Добавляем тестовые данные")
        
        # 1. Создаем здания
        buildings_data = [
            {
                "address": "г. Москва, ул. Тверская, д. 1",
                "latitude": 55.7558,
                "longitude": 37.6173
            },
            {
                "address": "г. Москва, ул. Арбат, д. 25",
                "latitude": 55.7495,
                "longitude": 37.5900
            },
            {
                "address": "г. Москва, пр-т Мира, д. 100",
                "latitude": 55.7810,
                "longitude": 37.6330
            },
            {
                "address": "г. Санкт-Петербург, Невский пр-т, д. 50",
                "latitude": 59.9343,
                "longitude": 30.3351
            },
            {
                "address": "г. Санкт-Петербург, ул. Садовая, д. 10",
                "latitude": 59.9311,
                "longitude": 30.3209
            }
        ]
        
        buildings = []
        for data in buildings_data:
            building = Building(**data)
            session.add(building)
            buildings.append(building)
        
        await session.flush()
        
        # 2. Создаем дерево видов деятельности
        activities_data = [
            # Уровень 1
            {"name": "Еда", "children": [ # 0
                # Уровень 2
                {"name": "Мясная продукция", "children": [ # 1
                    # Уровень 3
                    {"name": "Говядина"}, # 2
                    {"name": "Свинина"}, # 3
                    {"name": "Птица"}, # 4
                ]},
                {"name": "Молочная продукция", "children": [ # 5
                    {"name": "Молоко"}, # 6
                    {"name": "Сыр"}, # 7
                    {"name": "Йогурты"}, # 8
                ]},
                {"name": "Овощи и фрукты"}, # 9
                {"name": "Бакалея"}, # 10
            ]},
            {"name": "Автомобили", "children": [ # 11
                {"name": "Легковые автомобили"}, # 12
                {"name": "Грузовые автомобили"}, # 13
                {"name": "Запчасти", "children": [ # 14
                    {"name": "Двигатели"}, # 15
                    {"name": "Тормозная система"}, # 16
                    {"name": "Электрооборудование"}, # 17
                ]},
            ]},
            {"name": "Электроника", "children": []}, # 18
            {"name": "Одежда", "children": []} # 19
        ]
        
        activities = []
        for data in activities_data:
            activities_data = await create_activity_hierarchy(data=data, session=session)
            activities.extend(activities_data)
            
        await session.flush()
        
        # 3. Создаем организации
        organizations_data = [
            {
                "name": 'ООО "Рога и Копыта"',
                "building_id": buildings[0].id,
                "activities": [activities[1], activities[2]],  # Мясная продукция, Говядина
                "phone_numbers": ["8-800-555-35-35", "495-123-45-67"]
            },
            {
                "name": 'ЗАО "Молочные реки"',
                "building_id": buildings[1].id,
                "activities": [activities[0], activities[5], activities[7]],  # Еда, Молочная продукция, Сыр
                "phone_numbers": ["8-800-100-20-30", "495-987-65-43"]
            },
            {
                "name": 'ИП "АвтоМир"',
                "building_id": buildings[2].id,
                "activities": [activities[11], activities[12], activities[14]],  # Автомобили, Легковые автомобили, Запчасти
                "phone_numbers": ["8-800-200-30-40", "495-555-44-33"]
            },
            {
                "name": 'ОАО "Сыроварня"',
                "building_id": buildings[3].id,
                "activities": [activities[7], activities[8]],  # Сыр, Йогурты
                "phone_numbers": ["812-333-44-55", "812-666-77-88"]
            },
            {
                "name": 'ТК "Автозапчасти"',
                "building_id": buildings[4].id,
                "activities": [activities[14], activities[15]],  # Запчасти, Двигатели
                "phone_numbers": ["812-999-00-11", "812-222-33-44"]
            },
            {
                "name": 'ООО "Фруктовый рай"',
                "building_id": buildings[0].id,
                "activities": [activities[9]],  # Овощи и фрукты
                "phone_numbers": ["495-111-22-33"]
            },
            {
                "name": 'ИП "Электросила"',
                "building_id": buildings[1].id,
                "activities": [activities[18]],  # Электроника
                "phone_numbers": ["495-444-55-66", "495-777-88-99"]
            }
        ]
        
        for org_data in organizations_data:
            phone_numbers = org_data.pop("phone_numbers")
            activity_ids = org_data.pop("activities")
            
            organization = Organization(**org_data)
            session.add(organization)
            await session.flush()
            
            # Добавляем номера телефонов
            for phone in phone_numbers:
                phone_number = PhoneNumber(number=phone, organization_id=organization.id)
                session.add(phone_number)
            
            for activity_id in activity_ids:
                # Связываем с видами деятельности
                await session.execute(organization_activity.insert().values(
                    organization_id=organization.id,
                    activity_id=activity_id
                ))
        
        await session.commit()
        config.logger.info("Тестовые данные успешно добавлены!")
        
    except Exception as e:
        config.logger.error(f"Ошибка при заполнении базы данных: {e}")
        raise