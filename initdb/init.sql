-- Создаем пользователя если не существует
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'postgres') THEN
        CREATE USER postgres WITH SUPERUSER PASSWORD 'postgres';
    END IF;
END
$$;

-- Создаем базу данных если не существует
SELECT 'CREATE DATABASE directory'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'directory')\gexec

-- Даем права пользователю на базу данных
GRANT ALL PRIVILEGES ON DATABASE directory TO postgres;