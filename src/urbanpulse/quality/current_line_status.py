from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def invalid_current_line_status(
    df: DataFrame,
) -> DataFrame:

    return (
        df
        .filter(
            F.col("line_key").isNull()
            |
            F.col("line_id").isNull()
            |
            F.col("line_name").isNull()
            |
            F.col(
                "status_severity"
            ).isNull()
            |
            F.col(
                "status_snapshot_at_utc"
            ).isNull()
            |
            F.col(
                "is_good_service"
            ).isNull()
            |
            F.col(
                "is_disrupted"
            ).isNull()
        )
    )