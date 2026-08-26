from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def build_station_arrival_summary(
    fact_df: DataFrame,
    dim_station_df: DataFrame,
    dim_line_df: DataFrame,
) -> DataFrame:

    latest_prediction_at = (
        fact_df
        .agg(
            F.max(
                "prediction_timestamp"
            ).alias(
                "latest_prediction_at"
            )
        )
        .first()["latest_prediction_at"]
    )

    if latest_prediction_at is None:
        raise ValueError(
            "No arrival observations found."
        )

    latest_date = (
        fact_df
        .filter(
            F.col("prediction_timestamp")
            == latest_prediction_at
        )
        .select(
            F.to_date(
                F.from_utc_timestamp(
                    F.col(
                        "prediction_timestamp"
                    ),
                    "Europe/London",
                )
            ).alias("latest_date")
        )
        .first()["latest_date"]
    )

    latest_day_df = (
        fact_df
        .filter(
            F.to_date(
                F.from_utc_timestamp(
                    F.col(
                        "prediction_timestamp"
                    ),
                    "Europe/London",
                )
            )
            ==
            F.lit(latest_date)
        )
    )

    summary_df = (
        latest_day_df
        .groupBy(
            "station_key",
            "line_key",
            "requested_station_id",
            "line_id",
        )
        .agg(
            F.count("*").alias(
                "arrival_observations"
            ),

            F.countDistinct(
                "vehicle_id"
            ).alias(
                "distinct_vehicles"
            ),

            F.round(
                F.avg(
                    "time_to_station_seconds"
                ),
                1,
            ).alias(
                "avg_eta_seconds"
            ),

            F.min(
                "time_to_station_seconds"
            ).alias(
                "min_eta_seconds"
            ),

            F.max(
                "time_to_station_seconds"
            ).alias(
                "max_eta_seconds"
            ),

            F.min(
                "expected_arrival"
            ).alias(
                "next_expected_arrival_utc"
            ),

            F.max(
                "prediction_timestamp"
            ).alias(
                "latest_prediction_timestamp_utc"
            ),
        )
    )

    current_station_df = (
        dim_station_df
        .filter(
            F.col("is_current")
        )
        .select(
            "station_key",
            "station_id",
            "station_name",
            "latitude",
            "longitude",
        )
    )

    current_line_df = (
        dim_line_df
        .filter(
            F.col("is_current")
        )
        .select(
            "line_key",
            "line_id",
            "line_name",
        )
    )

    return (
        summary_df.alias("summary")
        .join(
            current_station_df.alias("station"),
            on="station_key",
            how="inner",
        )
        .join(
            current_line_df.alias("line"),
            on="line_key",
            how="inner",
        )
        .withColumn(
            "next_expected_arrival_local",
            F.from_utc_timestamp(
                F.col(
                    "next_expected_arrival_utc"
                ),
                "Europe/London",
            ),
        )
        .withColumn(
            "latest_prediction_timestamp_local",
            F.from_utc_timestamp(
                F.col(
                    "latest_prediction_timestamp_utc"
                ),
                "Europe/London",
            ),
        )
        .select(
            "station_key",
            "line_key",
            F.col(
                "station.station_id"
            ).alias(
                "station_id"
            ),
            F.col(
                "station.station_name"
            ).alias(
                "station_name"
            ),
            F.col(
                "station.latitude"
            ),
            F.col(
                "station.longitude"
            ),
            F.col(
                "line.line_id"
            ).alias(
                "line_id"
            ),
            F.col(
                "line.line_name"
            ).alias(
                "line_name"
            ),
            "arrival_observations",
            "distinct_vehicles",
            "avg_eta_seconds",
            "min_eta_seconds",
            "max_eta_seconds",
            "next_expected_arrival_utc",
            "next_expected_arrival_local",
            "latest_prediction_timestamp_utc",
            "latest_prediction_timestamp_local",
        )
    )