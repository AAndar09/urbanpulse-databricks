from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def prepare_line_source(
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
            "No TfL line-status snapshots found."
        )

    first_seen_df = (
        silver_df
        .groupBy("line_id")
        .agg(
            F.min("snapshot_at").alias(
                "first_seen_at"
            )
        )
    )

    source_df = (
        silver_df
        .filter(
            F.col("snapshot_at")
            == latest_snapshot
        )
        .select(
            "line_id",
            "line_name",
            "mode_name",
            "snapshot_at",
        )
        .dropDuplicates([
            "line_id",
            "line_name",
            "mode_name",
            "snapshot_at",
        ])
        .join(
            first_seen_df,
            on="line_id",
            how="left",
        )
        .withColumn(
            "is_active",
            F.lit(True),
        )
    )

    return (
        source_df
        .withColumn(
            "attribute_hash",
            F.sha2(
                F.concat_ws(
                    "||",
                    F.coalesce(
                        F.col("line_name"),
                        F.lit(""),
                    ),
                    F.coalesce(
                        F.col("mode_name"),
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