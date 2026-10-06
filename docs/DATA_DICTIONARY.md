# Data Dictionary

Automatically generated from PostgreSQL metadata.

## `mart.dim_city`

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `city_key` | `integer` | NO | |
| `city_name` | `character varying` | NO | |
| `latitude` | `numeric` | YES | |
| `longitude` | `numeric` | YES | |

## `mart.dim_date`

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `date_key` | `integer` | NO | |
| `full_date` | `date` | NO | |
| `year` | `integer` | NO | |
| `month` | `integer` | NO | |
| `day` | `integer` | NO | |
| `quarter` | `integer` | NO | |
| `month_name` | `character varying` | NO | |
| `day_of_week` | `integer` | NO | |
| `day_name` | `character varying` | NO | |

## `mart.fact_weather`

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `weather_key` | `bigint` | NO | |
| `city_key` | `integer` | NO | |
| `date_key` | `integer` | NO | |
| `weather_time` | `timestamp with time zone` | NO | |
| `temperature_c` | `numeric` | YES | |
| `humidity_pct` | `numeric` | YES | |
| `wind_speed_kmh` | `numeric` | YES | |
| `loaded_at` | `timestamp with time zone` | NO | |

## `raw.weather`

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `raw_id` | `bigint` | NO | |
| `city` | `character varying` | NO | |
| `collected_at` | `timestamp without time zone` | NO | |
| `source_file` | `character varying` | YES | |
| `raw_payload` | `jsonb` | NO | |
| `ingested_at` | `timestamp without time zone` | NO | |

## `staging.weather`

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `weather_id` | `bigint` | NO | |
| `city` | `character varying` | NO | |
| `weather_time` | `timestamp without time zone` | NO | |
| `temperature_c` | `numeric` | YES | |
| `humidity_pct` | `numeric` | YES | |
| `wind_speed_kmh` | `numeric` | YES | |
| `loaded_at` | `timestamp without time zone` | NO | |
| `source_file` | `character varying` | YES | |