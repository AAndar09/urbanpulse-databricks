from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def valid_stop_points(
    df: DataFrame,
) -> DataFrame:

    return (
        df
        .filter(
            F.col("request_id").isNotNull()
        )
        .filter(
            F.col("stop_point_id").isNotNull()
        )
        .filter(
            F.col("common_name").isNotNull()
        )
        .filter(
            F.col("latitude").between(
                -90.0,
                90.0,
            )
        )
        .filter(
            F.col("longitude").between(
                -180.0,
                180.0,
            )
        )
        .filter(
            F.col("snapshot_at").isNotNull()
        )
    )


def invalid_stop_points(
    df: DataFrame,
) -> DataFrame:

    return (
        df
        .filter(
            F.col("request_id").isNull()
            |
            F.col("stop_point_id").isNull()
            |
            F.col("common_name").isNull()
            |
            F.col("latitude").isNull()
            |
            F.col("longitude").isNull()
            |
            (~F.col("latitude").between(
                -90.0,
                90.0,
            ))
            |
            (~F.col("longitude").between(
                -180.0,
                180.0,
            ))
            |
            F.col("snapshot_at").isNull()
        )
    )