"""Create all tables if migrations not applied yet."""
from control_plane.app.infrastructure.db.session import engine, Base
from control_plane.app.infrastructure.db import models  # noqa: F401


def ensure_schema() -> None:
    Base.metadata.create_all(bind=engine)
