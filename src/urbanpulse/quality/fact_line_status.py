from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def invalid_fact_line_status(
    df: DataFrame,
) -> DataFrame:

    return (
        df
        .filter(
            F.col("line_status_key").isNull()
            |
            F.col("line_key").isNull()
            |
            F.col("line_id").isNull()
            |
            F.col("snapshot_date_key").isNull()
            |
            F.col("request_id").isNull()
            |
            F.col("snapshot_at").isNull()
            |
            F.col("status_severity").isNull()
        )
    )