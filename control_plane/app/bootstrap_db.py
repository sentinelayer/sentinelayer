from sqlalchemy.exc import ProgrammingError

import control_plane.app.infrastructure.db.models  # noqa: F401
from control_plane.app.infrastructure.db.session import Base, engine


def ensure_schema() -> None:
    try:
        Base.metadata.create_all(bind=engine)
    except ProgrammingError:
        pass
