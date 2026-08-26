import os

from databricks import sql
from databricks.sdk.core import Config


config = Config()


def get_connection():

    warehouse_id = os.getenv(
        "DATABRICKS_WAREHOUSE_ID"
    )

    if not warehouse_id:
        raise RuntimeError(
            "DATABRICKS_WAREHOUSE_ID is not configured. "
            "Check the SQL warehouse App resource key "
            "and app.yaml."
        )

    server_hostname = config.host

    server_hostname = (
        server_hostname
        .removeprefix("https://")
        .removeprefix("http://")
    )

    return sql.connect(
        server_hostname=server_hostname,
        http_path=(
            f"/sql/1.0/warehouses/"
            f"{warehouse_id}"
        ),
        credentials_provider=(
            lambda: config.authenticate
        ),
        _use_arrow_native_complex_types=False,
    )