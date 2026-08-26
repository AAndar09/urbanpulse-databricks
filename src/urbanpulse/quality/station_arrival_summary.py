from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def invalid_station_arrival_summary(
    df: DataFrame,
) -> DataFrame:

    return (
        df
        .filter(
            F.col("station_key").isNull()
            |
            F.col("line_key").isNull()
            |
            F.col("station_id").isNull()
            |
            F.col("station_name").isNull()
            |
            F.col("line_id").isNull()
            |
            F.col("line_name").isNull()
            |
            (
                F.col(
                    "arrival_observations"
                ) <= 0
            )
            |
            (
                F.col(
                    "distinct_vehicles"
                ) < 0
            )
            |
            (
                F.col(
                    "avg_eta_seconds"
                ) < 0
            )
            |
            (
                F.col(
                    "min_eta_seconds"
                ) < 0
            )
            |
            (
                F.col(
                    "max_eta_seconds"
                ) < 0
            )
            |
            F.col(
                "latest_prediction_timestamp_utc"
            ).isNull()
        )
    )