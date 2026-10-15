from scripts.verify_migration_target import ENVIRONMENT_ID, PROJECT_ID, validate


def valid():
    return {
        "RAILWAY_PROJECT_ID": PROJECT_ID,
        "RAILWAY_ENVIRONMENT_ID": ENVIRONMENT_ID,
        "SL_ENV": "production",
        "MIGRATION_DATABASE_URL": "postgresql://postgres:private@postgres.railway.internal:5432/railway",
        "RUNTIME_DATABASE_PASSWORD": "a" * 48,
        "AUTHENTICATION_DATABASE_PASSWORD": "b" * 48,
        "WORKER_DATABASE_PASSWORD": "c" * 48,
    }


def test_migration_target_accepts_dedicated_private_production_postgres():
    assert validate(valid()) == []


def test_migration_target_rejects_external_and_unrelated_databases():
    for url in ("https://db.example.com", "postgresql://postgres:secret@db.example.com:5432/railway",
                "postgresql://postgres:secret@localhost:5432/railway",
                "postgresql://postgres:secret@postgres.railway.internal:99999/railway"):
        data = valid()
        data["MIGRATION_DATABASE_URL"] = url
        assert validate(data)


def test_migration_target_rejects_wrong_project_environment_and_roles():
    for key, value in (("RAILWAY_PROJECT_ID", "another"),
                       ("RAILWAY_ENVIRONMENT_ID", "another"),
                       ("SL_ENV", "development"),
                       ("RUNTIME_DATABASE_PASSWORD", "weak")):
        data = valid()
        data[key] = value
        assert validate(data)


def test_migration_service_role_passwords_must_differ():
    data = valid()
    data["WORKER_DATABASE_PASSWORD"] = data["RUNTIME_DATABASE_PASSWORD"]
    assert "MIGRATION_SERVICE_PASSWORDS_MUST_DIFFER" in validate(data)
