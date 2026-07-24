import pytest
import os
from alembic.config import Config
from alembic import command

def test_auth_service_alembic_migrations(tmp_path):
    db_file = tmp_path / "auth_alembic_test.db"
    db_url = f"sqlite:///{db_file}"
    
    config = Config("auth-service/alembic.ini")
    config.set_main_option("script_location", "auth-service/alembic")
    config.set_main_option("sqlalchemy.url", db_url)
    
    command.upgrade(config, "head")
    assert db_file.exists()

    command.downgrade(config, "base")

def test_expense_service_alembic_migrations(tmp_path):
    db_file = tmp_path / "expense_alembic_test.db"
    db_url = f"sqlite:///{db_file}"
    
    config = Config("expense-service/alembic.ini")
    config.set_main_option("script_location", "expense-service/alembic")
    config.set_main_option("sqlalchemy.url", db_url)
    
    command.upgrade(config, "head")
    assert db_file.exists()

    command.downgrade(config, "base")

def test_category_service_alembic_migrations(tmp_path):
    db_file = tmp_path / "category_alembic_test.db"
    db_url = f"sqlite:///{db_file}"
    
    config = Config("category-service/alembic.ini")
    config.set_main_option("script_location", "category-service/alembic")
    config.set_main_option("sqlalchemy.url", db_url)
    
    command.upgrade(config, "head")
    assert db_file.exists()

    command.downgrade(config, "base")
