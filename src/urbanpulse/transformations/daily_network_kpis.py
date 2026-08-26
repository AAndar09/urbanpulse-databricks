from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def build_daily_network_kpis(
    line_status_df: DataFrame,
    arrival_df: DataFrame,
    weather_df: DataFrame,
    dim_date_df: DataFrame,
) -> DataFrame:

    # Reduce multiple status rows for the same
    # line and snapshot to one operational state.
    line_snapshot_df = (
        line_status_df
        .groupBy(
            "snapshot_date_key",
            "line_id",
            "snapshot_at",
        )
        .agg(
            F.max(
                F.col("is_disrupted").cast("int")
            ).alias("_is_disrupted")
        )
    )

    line_daily_df = (
        line_snapshot_df
        .groupBy("snapshot_date_key")
        .agg(
            F.count("*").alias(
                "line_snapshots"
            ),
            F.countDistinct(
                "line_id"
            ).alias(
                "distinct_lines_observed"
            ),
            F.sum(
                "_is_disrupted"
            ).alias(
                "disrupted_line_snapshots"
            ),
        )
        .withColumn(
            "good_service_line_snapshots",
            F.col("line_snapshots")
            - F.col("disrupted_line_snapshots"),
        )
        .withColumn(
            "disruption_rate_pct",
            F.round(
                F.lit(100.0)
                * F.col("disrupted_line_snapshots")
                / F.col("line_snapshots"),
                2,
            ),
        )
        .withColumnRenamed(
            "snapshot_date_key",
            "date_key",
        )
    )

    arrival_daily_df = (
        arrival_df
        .groupBy("prediction_date_key")
        .agg(
            F.count("*").alias(
                "arrival_observations"
            ),
            F.countDistinct(
                "vehicle_id"
            ).alias(
                "distinct_vehicles"
            ),
            F.countDistinct(
                "station_key"
            ).alias(
                "stations_observed"
            ),
            F.round(
                F.avg(
                    "time_to_station_seconds"
                ),
                1,
            ).alias(
                "avg_eta_seconds"
            ),
        )
        .withColumnRenamed(
            "prediction_date_key",
            "date_key",
        )
    )

    weather_daily_df = (
        weather_df
        .groupBy("observation_date_key")
        .agg(
            F.count("*").alias(
                "weather_observations"
            ),
            F.round(
                F.avg("temperature_c"),
                2,
            ).alias(
                "avg_temperature_c"
            ),
            F.round(
                F.min("temperature_c"),
                2,
            ).alias(
                "min_temperature_c"
            ),
            F.round(
                F.max("temperature_c"),
                2,
            ).alias(
                "max_temperature_c"
            ),
            F.round(
                F.avg(
                    "relative_humidity_pct"
                ),
                2,
            ).alias(
                "avg_relative_humidity_pct"
            ),
            F.round(
                F.sum("precipitation_mm"),
                2,
            ).alias(
                "total_precipitation_mm"
            ),
            F.round(
                F.max("wind_gusts_kmh"),
                2,
            ).alias(
                "max_wind_gust_kmh"
            ),
        )
        .withColumnRenamed(
            "observation_date_key",
            "date_key",
        )
    )

    # Include only dates represented by
    # at least one operational fact domain.
    active_dates_df = (
        line_daily_df
        .select("date_key")
        .unionByName(
            arrival_daily_df.select(
                "date_key"
            )
        )
        .unionByName(
            weather_daily_df.select(
                "date_key"
            )
        )
        .distinct()
    )

    result_df = (
        active_dates_df
        .join(
            dim_date_df.select(
                "date_key",
                "calendar_date",
                "year",
                "quarter",
                "month",
                "month_name",
                "day_of_week",
                "day_name",
                "is_weekend",
                "is_bank_holiday",
                "holiday_name",
            ),
            on="date_key",
            how="inner",
        )
        .join(
            line_daily_df,
            on="date_key",
            how="left",
        )
        .join(
            arrival_daily_df,
            on="date_key",
            how="left",
        )
        .join(
            weather_daily_df,
            on="date_key",
            how="left",
        )
    )

    count_columns = [
        "line_snapshots",
        "distinct_lines_observed",
        "disrupted_line_snapshots",
        "good_service_line_snapshots",
        "arrival_observations",
        "distinct_vehicles",
        "stations_observed",
        "weather_observations",
    ]

    return (
        result_df
        .fillna(
            0,
            subset=count_columns,
        )
        .orderBy("calendar_date")
    )