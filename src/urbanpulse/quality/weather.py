from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def valid_weather(
    df: DataFrame,
) -> DataFrame:

    return (
        df
        .filter(
            F.col("request_id").isNotNull()
        )
        .filter(
            F.col("weather_observed_at").isNotNull()
        )
        .filter(
            F.col("latitude").between(-90, 90)
        )
        .filter(
            F.col("longitude").between(-180, 180)
        )
        .filter(
            F.col("relative_humidity_pct").between(
                0,
                100,
            )
        )
        .filter(
            F.col("cloud_cover_pct").between(
                0,
                100,
            )
        )
        .filter(
            F.col("precipitation_mm") >= 0
        )
        .filter(
            F.col("rain_mm") >= 0
        )
        .filter(
            F.col("wind_speed_kmh") >= 0
        )
        .filter(
            F.col("wind_gusts_kmh") >= 0
        )
        .filter(
            F.col("snapshot_at").isNotNull()
        )
    )


def invalid_weather(
    df: DataFrame,
) -> DataFrame:

    valid_df = valid_weather(df)

    return df.join(
        valid_df.select("request_id"),
        on="request_id",
        how="left_anti",
    )