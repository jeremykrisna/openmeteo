import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


BACKUP_DIR = Path(
    os.getenv("BACKUP_DIR", "/backup")
)

POSTGRES_HOST = os.environ["POSTGRES_HOST"]
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.environ["POSTGRES_DB"]
POSTGRES_USER = os.environ["BACKUP_POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["BACKUP_POSTGRES_PASSWORD"]

BACKUP_RETENTION = int(
    os.getenv("BACKUP_RETENTION", "7")
)


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def fail(message: str) -> None:
    log(f"ERROR: {message}")
    sys.exit(1)


def validate_config() -> None:
    required = {
        "POSTGRES_HOST": POSTGRES_HOST,
        "POSTGRES_DB": POSTGRES_DB,
        "POSTGRES_USER": POSTGRES_USER,
        "POSTGRES_PASSWORD": POSTGRES_PASSWORD,
    }

    for key, value in required.items():
        if not value:
            fail(f"Missing required environment variable: {key}")

    if BACKUP_RETENTION < 1:
        fail("BACKUP_RETENTION must be at least 1")


def create_backup() -> Path:

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H%M%S"
    )

    backup_file = (
        BACKUP_DIR
        / f"{POSTGRES_DB}_{timestamp}.dump"
    )

    log("Starting PostgreSQL backup...")
    log(f"Database : {POSTGRES_DB}")
    log(f"Host     : {POSTGRES_HOST}")
    log(f"User     : {POSTGRES_USER}")
    log(f"Output   : {backup_file}")

    env = os.environ.copy()

    env["PGPASSWORD"] = POSTGRES_PASSWORD

    command = [
        "pg_dump",
        "-h",
        POSTGRES_HOST,
        "-p",
        POSTGRES_PORT,
        "-U",
        POSTGRES_USER,
        "-d",
        POSTGRES_DB,
        "-Fc",
        "-f",
        str(backup_file),
    ]

    try:
        result = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )

    except FileNotFoundError:
        fail(
            "pg_dump was not found. "
            "Make sure postgresql-client is installed."
        )

    except subprocess.CalledProcessError as exc:
        if exc.stderr:
            log(exc.stderr.strip())

        fail(
            f"pg_dump failed with exit code {exc.returncode}"
        )

    if result.stderr:
        log(result.stderr.strip())

    if not backup_file.exists():
        fail("Backup command succeeded but backup file was not created.")

    backup_size = backup_file.stat().st_size

    if backup_size == 0:
        backup_file.unlink(missing_ok=True)
        fail("Backup file is empty.")

    log(
        f"Backup completed successfully "
        f"({backup_size:,} bytes)."
    )

    return backup_file


def verify_backup(backup_file: Path) -> None:

    log("Verifying backup...")

    command = [
        "pg_restore",
        "--list",
        str(backup_file),
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )

    except FileNotFoundError:
        fail(
            "pg_restore was not found. "
            "Make sure postgresql-client is installed."
        )

    except subprocess.CalledProcessError as exc:
        if exc.stderr:
            log(exc.stderr.strip())

        fail("Backup verification failed.")

    if not result.stdout.strip():
        fail("Backup contains no PostgreSQL objects.")

    object_count = len(
        result.stdout.strip().splitlines()
    )

    log(
        f"Backup verification successful. "
        f"Objects found: {object_count}"
    )


def cleanup_old_backups() -> None:

    backups = sorted(
        BACKUP_DIR.glob("*.dump"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    log(
        f"Backup retention: keeping latest "
        f"{BACKUP_RETENTION} backup(s)."
    )

    for old_backup in backups[BACKUP_RETENTION:]:
        log(f"Removing old backup: {old_backup.name}")

        old_backup.unlink()


def main() -> None:

    log("========================================")
    log("PostgreSQL Backup")
    log("========================================")

    validate_config()

    backup_file = create_backup()

    verify_backup(backup_file)

    cleanup_old_backups()

    log("========================================")
    log("Backup process completed successfully.")
    log("========================================")


if __name__ == "__main__":
    main()