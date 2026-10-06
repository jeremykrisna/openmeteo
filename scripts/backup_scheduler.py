import subprocess
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


TIMEZONE = ZoneInfo("Asia/Jakarta")

BACKUP_HOUR = 3
BACKUP_MINUTE = 0


def log(message: str) -> None:
    now = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")

    print(
        f"[{now}] {message}",
        flush=True,
    )


def get_next_backup_time() -> datetime:
    now = datetime.now(TIMEZONE)

    next_backup = now.replace(
        hour=BACKUP_HOUR,
        minute=BACKUP_MINUTE,
        second=0,
        microsecond=0,
    )

    if next_backup <= now:
        next_backup += timedelta(days=1)

    return next_backup


def run_backup() -> None:
    log("Starting PostgreSQL backup...")

    subprocess.run(
        [
            "python3",
            "/app/backup_database.py",
        ],
        check=True,
    )

    log("PostgreSQL backup completed successfully.")


def main() -> None:
    log("Backup scheduler started.")
    log("Schedule: daily at 03:00 Asia/Jakarta.")

    while True:

        next_backup = get_next_backup_time()

        log(
            "Next backup: "
            f"{next_backup.strftime('%Y-%m-%d %H:%M:%S %Z')}"
        )

        now = datetime.now(TIMEZONE)

        wait_seconds = (
            next_backup - now
        ).total_seconds()

        log(
            f"Waiting {wait_seconds:.0f} seconds..."
        )

        time.sleep(wait_seconds)

        try:
            run_backup()

        except subprocess.CalledProcessError as exc:
            log(
                "Backup failed. "
                f"Exit code: {exc.returncode}"
            )


if __name__ == "__main__":
    main()