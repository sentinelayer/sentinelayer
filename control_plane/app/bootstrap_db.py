from sqlalchemy.exc import ProgrammingError

import importlib

importlib.import_module("control_plane.app.infrastructure.db.models")
from control_plane.app.infrastructure.db.session import Base, engine


def ensure_schema() -> None:
    try:
        Base.metadata.create_all(bind=engine)
    except ProgrammingError:
        pass
