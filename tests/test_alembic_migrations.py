import json
import subprocess
import sys

import pytest

EXPECTED = {
    "auth-service": ("users", {"id", "email", "first_name", "last_name", "hashed_password", "created_at"}),
    "expense-service": ("expenses", {"id", "user_id", "category_id", "title", "amount", "type", "date", "description", "created_at"}),
    "category-service": ("categories", {"id", "user_id", "name", "type", "created_at"}),
}


@pytest.mark.parametrize("service", sorted(EXPECTED))
def test_migrations_create_the_schema_the_models_expect(service, tmp_path):
    table, expected_columns = EXPECTED[service]
    db_url = f"sqlite:///{tmp_path / 'm.db'}"
    out = subprocess.run(
        [sys.executable, "tests/_alembic_inspect.py", service, db_url],
        capture_output=True, text=True, cwd=".",
    )
    assert out.returncode == 0, out.stderr
    upgraded, downgraded = [json.loads(line) for line in out.stdout.strip().splitlines()[-2:]]

    assert upgraded["tables"] == [table]
    assert set(upgraded["columns"][table]) == expected_columns
    # Models and migrations agree: a model change without a new migration fails here.
    assert upgraded["drift"] == [], f"models and migrations have drifted: {upgraded['drift']}"
    # Downgrade really removes what upgrade created.
    assert downgraded["after_downgrade"] == []
