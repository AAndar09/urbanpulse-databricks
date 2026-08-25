from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def build_current_line_status(
    fact_df: DataFrame,
    dim_line_df: DataFrame,
) -> DataFrame:

    latest_snapshot_df = (
        fact_df
        .groupBy("line_id")
        .agg(
            F.max("snapshot_at").alias(
                "latest_snapshot_at"
            )
        )
    )

    latest_fact_df = (
        fact_df.alias("fact")
        .join(
            latest_snapshot_df.alias("latest"),
            (
                F.col("fact.line_id")
                == F.col("latest.line_id")
            )
            &
            (
                F.col("fact.snapshot_at")
                == F.col(
                    "latest.latest_snapshot_at"
                )
            ),
            how="inner",
        )
        .select("fact.*")
    )

    status_df = (
        latest_fact_df
        .groupBy(
            "line_id",
            "snapshot_at",
        )
        .agg(
            F.min(
                "status_severity"
            ).alias(
                "status_severity"
            ),

            F.sort_array(
                F.collect_set(
                    "status_description"
                )
            ).alias(
                "_status_descriptions"
            ),

            F.sort_array(
                F.collect_set(
                    "status_reason"
                )
            ).alias(
                "_status_reasons"
            ),

            F.max(
                F.col(
                    "is_disrupted"
                ).cast("int")
            ).alias(
                "_is_disrupted"
            ),

            F.first(
                "request_id",
                ignorenulls=True,
            ).alias(
                "request_id"
            ),

            F.count("*").alias(
                "status_record_count"
            ),
        )
        .withColumn(
            "status_description",
            F.concat_ws(
                " | ",
                F.col(
                    "_status_descriptions"
                ),
            ),
        )
        .withColumn(
            "status_reason",
            F.when(
                F.size(
                    F.col("_status_reasons")
                ) > 0,
                F.concat_ws(
                    " | ",
                    F.col("_status_reasons"),
                ),
            ).otherwise(
                F.lit(None).cast("string")
            ),
        )
        .withColumn(
            "is_disrupted",
            F.col("_is_disrupted") == 1,
        )
        .withColumn(
            "is_good_service",
            ~F.col("is_disrupted"),
        )
        .withColumnRenamed(
            "snapshot_at",
            "status_snapshot_at_utc",
        )
        .withColumn(
            "status_snapshot_at_local",
            F.from_utc_timestamp(
                F.col(
                    "status_snapshot_at_utc"
                ),
                "Europe/London",
            ),
        )
        .drop(
            "_status_descriptions",
            "_status_reasons",
            "_is_disrupted",
        )
    )

    current_lines_df = (
        dim_line_df
        .filter(
            F.col("is_current")
        )
        .select(
            "line_key",
            "line_id",
            "line_name",
            "mode_name",
        )
    )

    return (
        current_lines_df
        .join(
            status_df,
            on="line_id",
            how="left",
        )
        .select(
            "line_key",
            "line_id",
            "line_name",
            "mode_name",
            "status_severity",
            "status_description",
            "status_reason",
            "is_good_service",
            "is_disrupted",
            "status_record_count",
            "status_snapshot_at_utc",
            "status_snapshot_at_local",
            "request_id",
        )
    )