SELECT
    COUNT(*) AS invalid_rows
FROM mart.fact_weather f
LEFT JOIN mart.dim_city c
    ON f.city_key = c.city_key
WHERE c.city_key IS NULL;

SELECT
    COUNT(*) AS invalid_rows
FROM mart.fact_weather f
LEFT JOIN mart.dim_date d
    ON f.date_key = d.date_key
WHERE d.date_key IS NULL;

SELECT
    c.city_name,
    COUNT(*) AS observation_count,
    MIN(f.weather_time) AS min_weather_time,
    MAX(f.weather_time) AS max_weather_time
FROM mart.fact_weather f
JOIN mart.dim_city c
    ON f.city_key = c.city_key
GROUP BY
    c.city_name
ORDER BY
    c.city_name;