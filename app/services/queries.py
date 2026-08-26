import os

from services.databricks_sql import (
    get_connection,
)


def run_query(query: str):

    with get_connection() as connection:

        with connection.cursor() as cursor:

            cursor.execute(query)

            return (
                cursor
                .fetchall_arrow()
                .to_pandas()
            )


def get_current_line_status():
    table_name = os.environ[
        "CURRENT_LINE_STATUS_TABLE"
    ]

    query = f"""
        SELECT
            line_key,
            line_id,
            line_name,
            mode_name,
            status_severity,
            status_description,
            status_reason,
            is_good_service,
            is_disrupted,
            status_snapshot_at_utc,
            status_snapshot_at_local,
            serving_updated_at

        FROM {table_name}

        ORDER BY line_name
    """

    return run_query(query)
    table_name = os.environ[
        "CURRENT_LINE_STATUS_TABLE"
    ]

    query = f"""
        SELECT
            line_id,
            line_name,
            status_description,
            status_reason,
            is_good_service,
            is_disrupted,
            status_snapshot_at_local
        FROM {table_name}
        ORDER BY line_name
    """

    return run_query(query)

def get_network_summary():

    table_name = os.environ[
        "CURRENT_LINE_STATUS_TABLE"
    ]

    query = f"""
        SELECT
            COUNT(*) AS total_lines,

            SUM(
                CASE
                    WHEN is_good_service THEN 1
                    ELSE 0
                END
            ) AS good_service_lines,

            SUM(
                CASE
                    WHEN is_disrupted THEN 1
                    ELSE 0
                END
            ) AS disrupted_lines,

            ROUND(
                100.0
                *
                SUM(
                    CASE
                        WHEN is_good_service THEN 1
                        ELSE 0
                    END
                )
                /
                COUNT(*),
                1
            ) AS good_service_pct

        FROM {table_name}
    """

    return run_query(query)

def get_latest_arrival_kpis():

    table_name = os.environ[
        "DAILY_NETWORK_KPIS_TABLE"
    ]

    query = f"""
        SELECT
            calendar_date,
            arrival_observations,
            distinct_vehicles,
            stations_observed,
            avg_eta_seconds

        FROM {table_name}

        WHERE arrival_observations > 0

        ORDER BY calendar_date DESC

        LIMIT 1
    """

    return run_query(query)

def get_latest_weather_kpis():

    table_name = os.environ[
        "DAILY_NETWORK_KPIS_TABLE"
    ]

    query = f"""
        SELECT
            calendar_date,
            avg_temperature_c,
            total_precipitation_mm,
            max_wind_gust_kmh

        FROM {table_name}

        WHERE weather_observations > 0

        ORDER BY calendar_date DESC

        LIMIT 1
    """

    return run_query(query)

def get_recent_network_trends():

    table_name = os.environ[
        "DAILY_NETWORK_KPIS_TABLE"
    ]

    query = f"""
        SELECT
            calendar_date,
            disruption_rate_pct,
            arrival_observations,
            avg_eta_seconds

        FROM {table_name}

        WHERE
            line_snapshots > 0
            OR arrival_observations > 0

        ORDER BY calendar_date DESC

        LIMIT 30
    """

    return run_query(query)