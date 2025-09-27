# Organization Directory API

REST API приложение для справочника организаций, зданий и видов деятельности.
Разработано на FastAPI с использованием PostgreSQL.

## 📋 Функциональность

- Организации - карточки компаний с телефонами, привязкой к зданию и видами деятельности
- Здания - информация об адресах и географических координатах
- Деятельности - древовидная классификация видов деятельности (до 3 уровней вложенности)

## 📦 Установка

### Требования

- Docker 20.10+
- Docker Compose 2.0+

### Быстрый запуск

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/asamarka-625/Organization-Directory-API.git
cd Organization-Directory-API
```

2. **Запуск с Docker Compose:**
```
# Сборка и запуск контейнеров
docker compose up --build

# Запуск в фоновом режиме
docker compose up -d

# Остановка контейнеров
docker compose down
```

3. **Доступ к приложению:**
```
После запуска приложение будет доступно по адресу:

- API Documentation: http://localhost:8000/docs
```

4. **Просмотр логов:**
```
docker compose logs -f web
docker compose logs -f db
```

## 📡 API Endpoints

### Получить организацию по ID
- **GET api/v1/organizations/{id_organization}**

### Организации в конкретном здании
- **GET api/v1/organizations/?building_id=1**

### Организации по виду деятельности
- **GET api/v1/organizations/?activity_id=1**

### Организации по названию деятельности (со вложениями)
- **GET api/v1/organizations/?activity_name=Еда**

### Поиск организаций по названию
- **GET api/v1/organizations/?name_organization=ОАО "Сыроварня"**

### Организации в географическом радиусе
- **GET api/v1/organizations/?lat=55.75&lon=37.61&radius=12**
