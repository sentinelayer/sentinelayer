from sqlalchemy.exc import ProgrammingError
from control_plane.app.infrastructure.db.session import engine, Base
import control_plane.app.infrastructure.db.models  # noqa: F401


def ensure_schema() -> None:
    try:
        Base.metadata.create_all(bind=engine)
    except ProgrammingError:
        pass
