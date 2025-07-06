from tortoise import Tortoise
import os

TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": os.getenv("DB_HOST", "postgres"),
                "port": os.getenv("DB_PORT", 5432),
                "user": os.getenv("DB_USER", "postgres"),
                "password": os.getenv("DB_PASSWORD", "postgres"),
                "database": os.getenv("DB_NAME", "carlemany_files"),
            }
        }
    },
    "apps": {
        "authentication": {
            "models": ["app.authentication.models", "aerich.models"],
            "default_connection": "default",
        },
        "files": {
            "models": ["app.files.models"],
            "default_connection": "default",
        }
    },
}


async def init_db():
    """Initialize Tortoise ORM"""
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()


async def close_db():
    """Close database connections"""
    await Tortoise.close_connections()