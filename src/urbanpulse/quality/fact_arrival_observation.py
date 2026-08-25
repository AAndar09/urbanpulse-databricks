from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def invalid_fact_arrival_observation(
    df: DataFrame,
) -> DataFrame:

    return (
        df
        .filter(
            F.col(
                "arrival_observation_key"
            ).isNull()
            |
            F.col(
                "station_key"
            ).isNull()
            |
            F.col(
                "line_key"
            ).isNull()
            |
            F.col(
                "requested_station_id"
            ).isNull()
            |
            F.col(
                "line_id"
            ).isNull()
            |
            F.col(
                "prediction_date_key"
            ).isNull()
            |
            F.col(
                "request_id"
            ).isNull()
            |
            F.col(
                "arrival_id"
            ).isNull()
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
            F.col(
                "snapshot_at"
            ).isNull()
        )
    )