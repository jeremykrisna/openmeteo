FROM python:3.13-slim AS python-runtime

FROM postgres:16

COPY --from=python-runtime /usr/local/bin/python3 /usr/local/bin/python3
COPY --from=python-runtime /usr/local/bin/python /usr/local/bin/python
COPY --from=python-runtime /usr/local/lib/python3.13 /usr/local/lib/python3.13
COPY --from=python-runtime /usr/local/lib/libpython3.13.so.1.0 /usr/local/lib/libpython3.13.so.1.0

ENV LD_LIBRARY_PATH=/usr/local/lib

WORKDIR /app

COPY scripts/backup_database.py /app/backup_database.py
COPY scripts/backup_scheduler.py /app/backup_scheduler.py

RUN mkdir -p /backup

ENTRYPOINT ["python3", "/app/backup_database.py"]