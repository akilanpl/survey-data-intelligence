from sqlalchemy import create_engine, inspect

from app.config import Settings
from app import db as database


def test_persistent_data_dir_also_holds_default_database(monkeypatch, tmp_path):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    config = Settings(_env_file=None, data_dir=tmp_path / "persistent")
    assert config.database_url == f"sqlite:///{tmp_path / 'persistent' / 'app.db'}"


def test_sqlite_memory_database_is_preserved():
    config = Settings(_env_file=None, database_url="sqlite:///:memory:")
    assert config.database_url == "sqlite:///:memory:"


def test_startup_creates_custom_sqlite_parent(monkeypatch, tmp_path):
    path = tmp_path / "disk" / "metadata" / "app.db"
    engine = create_engine(f"sqlite:///{path}")
    monkeypatch.setattr(database, "engine", engine)
    # Seed the isolated database, not the global test database.
    from sqlalchemy.orm import sessionmaker
    monkeypatch.setattr(database, "SessionLocal", sessionmaker(bind=engine))
    try:
        database.init_db()
        assert path.exists()
        assert "batches" in inspect(engine).get_table_names()
    finally:
        engine.dispose()
