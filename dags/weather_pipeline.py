from datetime import timedelta

import pendulum

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator
from openlineage.client.event_v2 import Dataset

from airflow.timetables.interval import CronDataIntervalTimetable

RAW_WEATHER = Dataset(
    "postgresql://postgres:5432",
    name="weather_db.raw.weather",
)

STAGING_WEATHER = Dataset(
    namespace="postgresql://postgres:5432",
    name="weather_db.staging.weather",
)

DIM_CITY = Dataset(
    namespace="postgresql://postgres:5432",
    name="weather_db.mart.dim_city",
)

DIM_DATE = Dataset(
    namespace="postgresql://postgres:5432",
    name="weather_db.mart.dim_date",
)

FACT_WEATHER = Dataset(
    namespace="postgresql://postgres:5432",
    name="weather_db.mart.fact_weather",
)


def on_failure_callback(context):
    dag_id = context["dag"].dag_id
    task_id = context["task_instance"].task_id
    run_id = context["run_id"]
    exception = context.get("exception")
    log_url = context["task_instance"].log_url

    print("=" * 60)
    print("WEATHER PIPELINE FAILURE")
    print("=" * 60)
    print(f"DAG       : {dag_id}")
    print(f"Task      : {task_id}")
    print(f"Run ID    : {run_id}")
    print(f"Exception : {exception}")
    print(f"Log       : {log_url}")
    print("=" * 60)


with DAG(
    dag_id="weather_pipeline",
    start_date=pendulum.datetime(
        2026, 10, 1, tz="Asia/Jakarta"
    ),
    schedule=CronDataIntervalTimetable(
        "0 */3 * * *",
        timezone="Asia/Jakarta",
    ),
    catchup=False,
    max_active_runs=1,
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    on_failure_callback=on_failure_callback,
    tags=["weather", "open-meteo", "data-pipeline"],
) as dag:

    extract_weather = BashOperator(
        task_id="extract_weather",
        bash_command=(
            "python /opt/airflow/src/weather.py "
            "{{ data_interval_start.in_timezone('Asia/Jakarta').strftime('%Y-%m-%dT%H:%M') }} "
            "{{ data_interval_end.in_timezone('Asia/Jakarta').strftime('%Y-%m-%dT%H:%M') }}"
        ),
        outlets=[RAW_WEATHER],
    )

    transform_staging = BashOperator(
        task_id="transform_staging",
        bash_command=(
            "python /opt/airflow/src/transform_load.py staging"
        ),
        inlets=[
            RAW_WEATHER,
        ],
        outlets=[
            STAGING_WEATHER,
        ],
    )

    data_quality_staging = BashOperator(
        task_id="data_quality_staging",
        bash_command=(
            "python /opt/airflow/src/data_quality_staging.py"
        ),
        inlets=[
            STAGING_WEATHER,
        ],
    )

    transform_mart = BashOperator(
        task_id="transform_mart",
        bash_command=(
            "python /opt/airflow/src/transform_load.py mart"
        ),
        inlets=[
            STAGING_WEATHER,
        ],
        outlets=[
            DIM_CITY,
            DIM_DATE,
            FACT_WEATHER,
        ],
    )

    data_quality_mart = BashOperator(
        task_id="data_quality_mart",
        bash_command=(
            "python /opt/airflow/src/data_quality_mart.py"
        ),
        inlets=[
            DIM_CITY,
            DIM_DATE,
            FACT_WEATHER,
        ],
    )

    extract_weather >> transform_staging >> data_quality_staging >> transform_mart >> data_quality_mart