{{ config(materialized='table') }}

SELECT
    generated_at,
    headline,
    commentary,
    titles_mentioned,
    top_title,
    top_media_type,
    anomaly_detected,
    anomaly_type,
    severity,
    DATE(generated_at) AS insight_date,
    HOUR(generated_at) AS insight_hour
FROM media_pulse.raw.media_ai_insights
ORDER BY generated_at DESC