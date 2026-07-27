from api.routes.apis import router as apis_router
from api.routes.auth import router as auth_router
from api.routes.changes import router as changes_router
from api.routes.repos import router as repos_router
from api.routes.settings import router as settings_router
from api.routes.specs import router as specs_router

__all__ = [
    "apis_router",
    "auth_router",
    "changes_router",
    "repos_router",
    "settings_router",
    "specs_router",
]
