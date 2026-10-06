SELECT
    COUNT(*) AS invalid_rows
FROM staging.weather
WHERE city IS NULL
   OR TRIM(city) = ''
   OR weather_time IS NULL
   OR temperature_c IS NULL
   OR humidity_pct IS NULL
   OR wind_speed_kmh IS NULL;


SELECT
    city,
    weather_time,
    COUNT(*) AS duplicate_count
FROM staging.weather
GROUP BY
    city,
    weather_time
HAVING COUNT(*) > 1;


SELECT
    COUNT(*) AS invalid_rows
FROM staging.weather
WHERE humidity_pct < 0
   OR humidity_pct > 100;


SELECT
    COUNT(*) AS invalid_rows
FROM staging.weather
WHERE wind_speed_kmh < 0;

SELECT
    COUNT(*) AS invalid_rows
FROM staging.weather
WHERE temperature_c < -50
   OR temperature_c > 60;