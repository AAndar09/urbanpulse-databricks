from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def build_fact_line_status(
    silver_df: DataFrame,
    dim_line_df: DataFrame,
    dim_date_df: DataFrame,
) -> DataFrame:

    source_df = (
        silver_df
        .withColumn(
            "line_status_key",
            F.sha2(
                F.concat_ws(
                    "||",
                    F.col("request_id"),
                    F.col("line_id"),
                    F.coalesce(
                        F.col("status_id")
                        .cast("string"),
                        F.lit("NULL"),
                    ),
                ),
                256,
            ),
        )
        .withColumn(
            "snapshot_local_date",
            F.to_date(
                F.from_utc_timestamp(
                    F.col("snapshot_at"),
                    "Europe/London",
                )
            ),
        )
    )

    with_line_df = (
        source_df.alias("fact")
        .join(
            dim_line_df.alias("line"),
            (
                F.col("fact.line_id")
                ==
                F.col("line.line_id")
            )
            &
            (
                F.col("fact.snapshot_at")
                >=
                F.col("line.effective_from")
            )
            &
            (
                F.col("line.effective_to").isNull()
                |
                (
                    F.col("fact.snapshot_at")
                    <
                    F.col("line.effective_to")
                )
            ),
            how="inner",
        )
    )

    result_df = (
        with_line_df
        .join(
            dim_date_df.alias("date"),
            F.col(
                "fact.snapshot_local_date"
            )
            ==
            F.col("date.calendar_date"),
            how="inner",
        )
        .select(
            F.col(
                "fact.line_status_key"
            ),

            F.col(
                "line.line_key"
            ),

            F.col(
                "fact.line_id"
            ),

            F.col(
                "date.date_key"
            ).alias(
                "snapshot_date_key"
            ),

            F.col(
                "fact.request_id"
            ),

            F.col(
                "fact.snapshot_at"
            ),

            F.col(
                "fact.status_id"
            ),

            F.col(
                "fact.status_severity"
            ),

            F.col(
                "fact.status_description"
            ),

            F.col(
                "fact.status_reason"
            ),

            F.col(
                "fact.status_created_at"
            ),

            F.when(
                F.col(
                    "fact.status_severity"
                ) == 10,
                F.lit(True),
            )
            .otherwise(
                F.lit(False)
            )
            .alias(
                "is_good_service"
            ),

            F.when(
                F.col(
                    "fact.status_severity"
                ) == 10,
                F.lit(False),
            )
            .otherwise(
                F.lit(True)
            )
            .alias(
                "is_disrupted"
            ),

            F.col(
                "fact.source"
            ),
        )
    )

    return result_df