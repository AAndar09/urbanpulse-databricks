import os

from databricks import sql
from databricks.sdk.core import Config


def clean_hostname(host):
    return (
        host
        .removeprefix("https://")
        .removeprefix("http://")
        .rstrip("/")
    )


def get_connection():
    # -----------------------------------------------------
    # External hosting
    # Plotly Cloud / local external deployment
    # -----------------------------------------------------

    external_host = os.getenv(
        "DATABRICKS_SERVER_HOSTNAME"
    )

    external_http_path = os.getenv(
        "DATABRICKS_HTTP_PATH"
    )

    external_token = os.getenv(
        "DATABRICKS_TOKEN"
    )


    if any(
        [
            external_host,
            external_http_path,
            external_token,
        ]
    ):
        if not all(
            [
                external_host,
                external_http_path,
                external_token,
            ]
        ):
            raise RuntimeError(
                "External Databricks authentication "
                "is incomplete. Configure "
                "DATABRICKS_SERVER_HOSTNAME, "
                "DATABRICKS_HTTP_PATH and "
                "DATABRICKS_TOKEN."
            )

        return sql.connect(
            server_hostname=clean_hostname(
                external_host
            ),
            http_path=external_http_path,
            access_token=external_token,
            _use_arrow_native_complex_types=False,
        )


    # -----------------------------------------------------
    # Native Databricks Apps hosting
    # -----------------------------------------------------

    warehouse_id = os.getenv(
        "DATABRICKS_WAREHOUSE_ID"
    )

    if not warehouse_id:
        raise RuntimeError(
            "DATABRICKS_WAREHOUSE_ID is not configured."
        )


    config = Config()

    server_hostname = clean_hostname(
        config.host
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