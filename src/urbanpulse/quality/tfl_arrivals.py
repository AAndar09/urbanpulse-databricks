from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def valid_tfl_arrivals(
    df: DataFrame,
) -> DataFrame:

    return (
        df
        .filter(
            F.col("request_id").isNotNull()
        )
        .filter(
            F.col(
                "requested_stop_point_id"
            ) != ""
        )
        .filter(
            F.col("arrival_id").isNotNull()
        )
        .filter(
            F.col("line_id").isNotNull()
        )
        .filter(
            F.col("station_name").isNotNull()
        )
        .filter(
            F.col(
                "prediction_timestamp"
            ).isNotNull()
        )
        .filter(
            F.col(
                "expected_arrival"
            ).isNotNull()
        )
        .filter(
            F.col(
                "time_to_station_seconds"
            ).isNotNull()
        )
        .filter(
            F.col(
                "time_to_station_seconds"
            ) >= 0
        )
        .filter(
            F.col("snapshot_at").isNotNull()
        )
    )


def invalid_tfl_arrivals(
    df: DataFrame,
) -> DataFrame:

    return (
        df
        .filter(
            F.col("request_id").isNull()
            |
            (F.col(
                "requested_stop_point_id"
            ) == "")
            |
            F.col("arrival_id").isNull()
            |
            F.col("line_id").isNull()
            |
            F.col("station_name").isNull()
            |
            F.col(
                "prediction_timestamp"
            ).isNull()
            |
            F.col(
                "expected_arrival"
            ).isNull()
            |
            F.col(
                "time_to_station_seconds"
            ).isNull()
            |
            (
                F.col(
                    "time_to_station_seconds"
                ) < 0
            )
            |
            F.col("snapshot_at").isNull()
        )
    )