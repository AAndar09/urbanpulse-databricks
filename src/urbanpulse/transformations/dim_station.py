from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window


def prepare_station_source(
    silver_df: DataFrame,
) -> DataFrame:

    latest_snapshot = (
        silver_df
        .agg(
            F.max("snapshot_at").alias(
                "latest_snapshot"
            )
        )
        .first()["latest_snapshot"]
    )

    if latest_snapshot is None:
        raise ValueError(
            "No TfL stop-point snapshots found."
        )

    latest_df = (
        silver_df
        .filter(
            F.col("snapshot_at")
            == latest_snapshot
        )
        .filter(
            F.col("station_naptan").isNotNull()
        )
        .filter(
            F.trim(
                F.col("station_naptan")
            ) != ""
        )
        .withColumn(
            "modes",
            F.sort_array(
                F.col("modes")
            ),
        )
    )

    # Prefer a source row whose stop-point ID
    # matches the canonical station NAPTAN.
    #
    # If none exists, use a deterministic
    # fallback based on stop-point ID.
    station_window = (
        Window
        .partitionBy(
            "station_naptan"
        )
        .orderBy(
            F.when(
                F.col("stop_point_id")
                ==
                F.col("station_naptan"),
                F.lit(0),
            )
            .otherwise(F.lit(1))
            .asc(),
            F.col(
                "stop_point_id"
            ).asc(),
        )
    )

    canonical_df = (
        latest_df
        .withColumn(
            "_station_rank",
            F.row_number().over(
                station_window
            ),
        )
        .filter(
            F.col("_station_rank") == 1
        )
        .drop("_station_rank")
        .select(
            F.col(
                "station_naptan"
            ).alias(
                "station_id"
            ),

            F.col(
                "stop_point_id"
            ).alias(
                "representative_stop_point_id"
            ),

            F.col(
                "common_name"
            ).alias(
                "station_name"
            ),

            "latitude",
            "longitude",
            "stop_type",
            "modes",

            F.col(
                "snapshot_at"
            ),

            F.lit(True).alias(
                "is_active"
            ),
        )
    )

    return (
        canonical_df
        .withColumn(
            "attribute_hash",
            F.sha2(
                F.concat_ws(
                    "||",

                    F.coalesce(
                        F.col("station_name"),
                        F.lit(""),
                    ),

                    F.coalesce(
                        F.col("latitude")
                        .cast("string"),
                        F.lit(""),
                    ),

                    F.coalesce(
                        F.col("longitude")
                        .cast("string"),
                        F.lit(""),
                    ),

                    F.coalesce(
                        F.col("stop_type"),
                        F.lit(""),
                    ),

                    F.coalesce(
                        F.concat_ws(
                            ",",
                            F.col("modes"),
                        ),
                        F.lit(""),
                    ),

                    F.col(
                        "is_active"
                    ).cast("string"),
                ),
                256,
            ),
        )
    )