CREATE TABLE IF NOT EXISTS staging.weather_quarantine (
    city VARCHAR(100) NOT NULL,
    weather_time TIMESTAMP NOT NULL,
    temperature_c DOUBLE PRECISION,
    humidity_pct DOUBLE PRECISION,
    wind_speed_kmh DOUBLE PRECISION,
    source_file TEXT,
    failure_reason TEXT NOT NULL,
    quarantined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (city, weather_time)
);