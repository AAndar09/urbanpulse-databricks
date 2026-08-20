from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def valid_tfl_line_status(
    df: DataFrame,
) -> DataFrame:

    return (
        df
        .filter(
            F.col("request_id").isNotNull()
        )
        .filter(
            F.col("line_id").isNotNull()
        )
        .filter(
            F.col("line_name").isNotNull()
        )
        .filter(
            F.col("snapshot_at").isNotNull()
        )
        .filter(
            F.col("status_severity").isNotNull()
        )
    )


def invalid_tfl_line_status(
    df: DataFrame,
) -> DataFrame:

    return (
        df
        .filter(
            F.col("request_id").isNull()
            |
            F.col("line_id").isNull()
            |
            F.col("line_name").isNull()
            |
            F.col("snapshot_at").isNull()
            |
            F.col("status_severity").isNull()
        )
    )