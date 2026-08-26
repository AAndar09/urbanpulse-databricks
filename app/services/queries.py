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