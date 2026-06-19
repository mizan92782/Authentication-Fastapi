import pkgutil
import importlib
from tortoise import Tortoise
from app.core.config import settings


def discover_models() -> list[str]:
    import app.modules as modules_pkg
    found = ["aerich.models"]
    for _, module_name, _ in pkgutil.iter_modules(modules_pkg.__path__):
        module_path = f"app.modules.{module_name}.models"
        try:
            importlib.import_module(module_path)
            found.append(module_path)
        except ModuleNotFoundError:
            pass
    return found

TORTOISE_ORM_CONFIG = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": settings.db_host,
                "port": settings.db_port,
                "user": settings.db_user,
                "password": settings.db_password,
                "database": settings.db_name,
                "minsize": settings.db_min_connections,
                "maxsize": settings.db_max_connections,
            },
        }
    },
    "apps": {
        "models": {
            "models": discover_models(),
            "default_connection": "default",
        }
    },
    "use_tz": True,
    "timezone": "UTC",
}


async def init_db() -> None:
    await Tortoise.init(config=TORTOISE_ORM_CONFIG)


async def close_db() -> None:
    await Tortoise.close_connections()
