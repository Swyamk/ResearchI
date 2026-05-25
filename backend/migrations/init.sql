-- NutriMind Initial Database Setup
-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fast text search

-- Performance indexes (created after Alembic migrations)
-- These are handled by Alembic, this file runs before migrations for extensions only
