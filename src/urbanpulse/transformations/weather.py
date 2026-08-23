from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)


WEATHER_SCHEMA = StructType([
    StructField(
        "latitude",
        DoubleType(),
        True,
    ),
    StructField(
        "longitude",
        DoubleType(),
        True,
    ),
    StructField(
        "generationtime_ms",
        DoubleType(),
        True,
    ),
    StructField(
        "utc_offset_seconds",
        IntegerType(),
        True,
    ),
    StructField(
        "timezone",
        StringType(),
        True,
    ),
    StructField(
        "timezone_abbreviation",
        StringType(),
        True,
    ),
    StructField(
        "elevation",
        DoubleType(),
        True,
    ),
    StructField(
        "current_units",
        StructType([
            StructField("time", StringType(), True),
            StructField("interval", StringType(), True),
            StructField("temperature_2m", StringType(), True),
            StructField("relative_humidity_2m", StringType(), True),
            StructField("precipitation", StringType(), True),
            StructField("rain", StringType(), True),
            StructField("weather_code", StringType(), True),
            StructField("cloud_cover", StringType(), True),
            StructField("wind_speed_10m", StringType(), True),
            StructField("wind_gusts_10m", StringType(), True),
        ]),
        True,
    ),
    StructField(
        "current",
        StructType([
            StructField("time", StringType(), True),
            StructField("interval", IntegerType(), True),
            StructField("temperature_2m", DoubleType(), True),
            StructField("relative_humidity_2m", IntegerType(), True),
            StructField("precipitation", DoubleType(), True),
            StructField("rain", DoubleType(), True),
            StructField("weather_code", IntegerType(), True),
            StructField("cloud_cover", IntegerType(), True),
            StructField("wind_speed_10m", DoubleType(), True),
            StructField("wind_gusts_10m", DoubleType(), True),
        ]),
        True,
    ),
])


def weather_code_description():
    code = F.col("weather_code")

    return (
        F.when(code == 0, "Clear sky")
        .when(code.isin(1, 2, 3), "Cloudy")
        .when(code.isin(45, 48), "Fog")
        .when(code.isin(51, 53, 55), "Drizzle")
        .when(code.isin(56, 57), "Freezing drizzle")
        .when(code.isin(61, 63, 65), "Rain")
        .when(code.isin(66, 67), "Freezing rain")
        .when(code.isin(71, 73, 75, 77), "Snow")
        .when(code.isin(80, 81, 82), "Rain showers")
        .when(code.isin(85, 86), "Snow showers")
        .when(code.isin(95, 96, 99), "Thunderstorm")
        .otherwise("Unknown")
    )


def transform_weather(
    bronze_df: DataFrame,
) -> DataFrame:

    parsed_df = (
        bronze_df
        .withColumn(
            "weather",
            F.from_json(
                F.col("payload"),
                WEATHER_SCHEMA,
            ),
        )
    )

    weather_df = (
        parsed_df
        .select(
            F.col("request_id"),

            F.col(
                "weather.latitude"
            ).alias("latitude"),

            F.col(
                "weather.longitude"
            ).alias("longitude"),

            F.col(
                "weather.timezone"
            ).alias("weather_timezone"),

            F.col(
                "weather.utc_offset_seconds"
            ).alias("utc_offset_seconds"),

            F.col(
                "weather.current.time"
            ).alias(
                "weather_observed_at_local_raw"
            ),

            F.col(
                "weather.current.temperature_2m"
            ).alias("temperature_c"),

            F.col(
                "weather.current.relative_humidity_2m"
            ).alias("relative_humidity_pct"),

            F.col(
                "weather.current.precipitation"
            ).alias("precipitation_mm"),

            F.col(
                "weather.current.rain"
            ).alias("rain_mm"),

            F.col(
                "weather.current.weather_code"
            ).alias("weather_code"),

            F.col(
                "weather.current.cloud_cover"
            ).alias("cloud_cover_pct"),

            F.col(
                "weather.current.wind_speed_10m"
            ).alias("wind_speed_kmh"),

            F.col(
                "weather.current.wind_gusts_10m"
            ).alias("wind_gusts_kmh"),

            F.col(
                "weather.current.interval"
            ).alias("measurement_interval_seconds"),

            F.col(
                "ingested_at"
            ).alias("snapshot_at"),

            F.col("ingestion_date"),
            F.col("source"),
        )
    )

    weather_df = (
        weather_df
        .withColumn(
            "weather_observed_at_local",
            F.to_timestamp(
                "weather_observed_at_local_raw"
            ),
        )
        .withColumn(
            "weather_observed_at",
            F.to_utc_timestamp(
                F.col(
                    "weather_observed_at_local"
                ),
                "Europe/London",
            ),
        )
        .withColumn(
            "weather_description",
            weather_code_description(),
        )
        .drop(
            "weather_observed_at_local_raw"
        )
    )

    return weather_df