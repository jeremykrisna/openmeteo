CREATE TABLE IF NOT EXISTS raw.weather (
    raw_id BIGSERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    collected_at TIMESTAMP NOT NULL,
    source_file VARCHAR(255),
    raw_payload JSONB NOT NULL,
    ingested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staging.weather (
    weather_id BIGSERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    weather_time TIMESTAMP NOT NULL,
    temperature_c NUMERIC(5,2),
    humidity_pct NUMERIC(5,2),
    wind_speed_kmh NUMERIC(6,2),
    loaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_file VARCHAR(255),
    CONSTRAINT uq_staging_weather_city_time
        UNIQUE (city, weather_time)
);

CREATE TABLE IF NOT EXISTS mart.dim_city (
    city_key INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL,
    latitude NUMERIC(9,6),
    longitude NUMERIC(9,6),
    CONSTRAINT uq_dim_city_city_name
        UNIQUE (city_name)
);

CREATE TABLE IF NOT EXISTS mart.dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    CONSTRAINT uq_dim_date_full_date
        UNIQUE (full_date)
);

CREATE TABLE IF NOT EXISTS mart.fact_weather (
    weather_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    city_key INTEGER NOT NULL,
    date_key INTEGER NOT NULL,
    weather_time TIMESTAMPTZ NOT NULL,
    temperature_c NUMERIC(5,2),
    humidity_pct NUMERIC(5,2),
    wind_speed_kmh NUMERIC(6,2),
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_fact_weather_city
        FOREIGN KEY (city_key)
        REFERENCES mart.dim_city (city_key),
    CONSTRAINT fk_fact_weather_date
        FOREIGN KEY (date_key)
        REFERENCES mart.dim_date (date_key),
    CONSTRAINT uq_fact_weather_city_time
        UNIQUE (city_key, weather_time)
);