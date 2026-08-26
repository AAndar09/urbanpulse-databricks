from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def invalid_daily_network_kpis(
    df: DataFrame,
) -> DataFrame:

    return (
        df
        .filter(
            F.col("date_key").isNull()
            |
            F.col("calendar_date").isNull()
            |
            (
                F.col("line_snapshots") < 0
            )
            |
            (
                F.col(
                    "disrupted_line_snapshots"
                )
                >
                F.col("line_snapshots")
            )
            |
            (
                F.col(
                    "good_service_line_snapshots"
                )
                >
                F.col("line_snapshots")
            )
            |
            (
                F.col("disruption_rate_pct").isNotNull()
                &
                (
                    ~F.col(
                        "disruption_rate_pct"
                    ).between(
                        0,
                        100,
                    )
                )
            )
            |
            (
                F.col("arrival_observations") < 0
            )
            |
            (
                F.col("distinct_vehicles") < 0
            )
            |
            (
                F.col("stations_observed") < 0
            )
            |
            (
                F.col("avg_eta_seconds").isNotNull()
                &
                (
                    F.col("avg_eta_seconds") < 0
                )
            )
            |
            (
                F.col(
                    "total_precipitation_mm"
                ).isNotNull()
                &
                (
                    F.col(
                        "total_precipitation_mm"
                    ) < 0
                )
            )
            |
            (
                F.col(
                    "max_wind_gust_kmh"
                ).isNotNull()
                &
                (
                    F.col(
                        "max_wind_gust_kmh"
                    ) < 0
                )
            )
        )
    )