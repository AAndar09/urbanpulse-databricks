from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def build_fact_weather(
    silver_df: DataFrame,
    dim_date_df: DataFrame,
) -> DataFrame:

    source_df = (
        silver_df
        .withColumn(
            "observation_local_date",
            F.to_date(
                F.from_utc_timestamp(
                    F.col("weather_observed_at"),
                    "Europe/London",
                )
            ),
        )
    )

    return (
        source_df.alias("weather")
        .join(
            dim_date_df.alias("date"),
            F.col(
                "weather.observation_local_date"
            )
            ==
            F.col(
                "date.calendar_date"
            ),
            how="inner",
        )
        .select(
            F.col(
                "weather.weather_observation_key"
            ),

            F.col(
                "date.date_key"
            ).alias(
                "observation_date_key"
            ),

            F.col(
                "weather.weather_observed_at"
            ),

            F.col(
                "weather.weather_observed_at_local"
            ),

            F.col(
                "weather.latitude"
            ),

            F.col(
                "weather.longitude"
            ),

            F.col(
                "weather.weather_timezone"
            ),

            F.col(
                "weather.utc_offset_seconds"
            ),

            F.col(
                "weather.temperature_c"
            ),

            F.col(
                "weather.relative_humidity_pct"
            ),

            F.col(
                "weather.precipitation_mm"
            ),

            F.col(
                "weather.rain_mm"
            ),

            F.col(
                "weather.weather_code"
            ),

            F.col(
                "weather.weather_description"
            ),

            F.col(
                "weather.cloud_cover_pct"
            ),

            F.col(
                "weather.wind_speed_kmh"
            ),

            F.col(
                "weather.wind_gusts_kmh"
            ),

            F.col(
                "weather.measurement_interval_seconds"
            ),

            F.col(
                "weather.snapshot_at"
            ),

            F.col(
                "weather.source"
            ),
        )
    )