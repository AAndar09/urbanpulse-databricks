from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def invalid_fact_weather(
    df: DataFrame,
) -> DataFrame:

    return (
        df
        .filter(
            F.col(
                "weather_observation_key"
            ).isNull()
            |
            F.col(
                "observation_date_key"
            ).isNull()
            |
            F.col(
                "weather_observed_at"
            ).isNull()
            |
            F.col(
                "latitude"
            ).isNull()
            |
            F.col(
                "longitude"
            ).isNull()
            |
            (~F.col(
                "latitude"
            ).between(
                -90,
                90,
            ))
            |
            (~F.col(
                "longitude"
            ).between(
                -180,
                180,
            ))
            |
            F.col(
                "temperature_c"
            ).isNull()
            |
            F.col(
                "relative_humidity_pct"
            ).isNull()
            |
            (~F.col(
                "relative_humidity_pct"
            ).between(
                0,
                100,
            ))
            |
            (
                F.col(
                    "precipitation_mm"
                ) < 0
            )
            |
            (
                F.col(
                    "rain_mm"
                ) < 0
            )
            |
            (~F.col(
                "cloud_cover_pct"
            ).between(
                0,
                100,
            ))
            |
            (
                F.col(
                    "wind_speed_kmh"
                ) < 0
            )
            |
            (
                F.col(
                    "wind_gusts_kmh"
                ) < 0
            )
            |
            F.col(
                "snapshot_at"
            ).isNull()
        )
    )