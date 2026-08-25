import subprocess
import sys

def run_migrations():
    try:
        result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Migration failed: {result.stderr}")
            sys.exit(1)
        print("Migrations applied successfully")
    except Exception as e:
        print(f"Error running migrations: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()
