from athena_client import run_query

df = run_query(
    """
    SELECT satellite_id, COUNT(*) AS event_count
    FROM silver_telemetry
    GROUP BY satellite_id
    """
)

print(df)