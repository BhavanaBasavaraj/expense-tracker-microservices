"""Helper run in a subprocess (each service has a top-level package named `app`, so they
cannot be imported side by side in one process).

usage: python tests/_alembic_inspect.py <service-dir> <sqlite-url>
Applies migrations to head, then prints JSON: tables, columns, and any drift between the
migrated schema and the SQLAlchemy models (alembic's compare_metadata).
"""
import json
import os
import sys

service_dir, db_url = sys.argv[1], sys.argv[2]
os.chdir(service_dir)
sys.path.insert(0, os.getcwd())
os.environ["DATABASE_URL"] = db_url

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect

cfg = Config("alembic.ini")
# The database URL is NOT injected into the alembic config here. It must come from the
# DATABASE_URL env var, exactly as it does inside a container (injecting it hid a real bug).
command.upgrade(cfg, "head")

from app.database import Base
import app.models  # noqa: F401  (registers tables on Base.metadata)

engine = create_engine(db_url)
insp = inspect(engine)
tables = sorted(t for t in insp.get_table_names() if t != "alembic_version")
columns = {t: sorted(c["name"] for c in insp.get_columns(t)) for t in tables}
with engine.connect() as conn:
    diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
print(json.dumps({"tables": tables, "columns": columns, "drift": [repr(d) for d in diff]}))

command.downgrade(cfg, "base")
left = [t for t in inspect(create_engine(db_url)).get_table_names() if t != "alembic_version"]
print(json.dumps({"after_downgrade": left}))
