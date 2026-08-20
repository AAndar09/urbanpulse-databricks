from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import (
    ArrayType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)


LINE_STATUS_SCHEMA = ArrayType(
    StructType([
        StructField(
            "id",
            StringType(),
            True,
        ),
        StructField(
            "name",
            StringType(),
            True,
        ),
        StructField(
            "modeName",
            StringType(),
            True,
        ),
        StructField(
            "lineStatuses",
            ArrayType(
                StructType([
                    StructField(
                        "id",
                        IntegerType(),
                        True,
                    ),
                    StructField(
                        "statusSeverity",
                        IntegerType(),
                        True,
                    ),
                    StructField(
                        "statusSeverityDescription",
                        StringType(),
                        True,
                    ),
                    StructField(
                        "reason",
                        StringType(),
                        True,
                    ),
                    StructField(
                        "created",
                        StringType(),
                        True,
                    ),
                ])
            ),
            True,
        ),
    ])
)


def transform_tfl_line_status(
    bronze_df: DataFrame,
) -> DataFrame:

    parsed_df = (
        bronze_df
        .withColumn(
            "parsed_payload",
            F.from_json(
                F.col("payload"),
                LINE_STATUS_SCHEMA,
            ),
        )
    )

    lines_df = (
        parsed_df
        .withColumn(
            "line",
            F.explode_outer(
                F.col("parsed_payload")
            ),
        )
    )

    statuses_df = (
        lines_df
        .withColumn(
            "line_status",
            F.explode_outer(
                F.col("line.lineStatuses")
            ),
        )
    )

    silver_df = (
        statuses_df
        .select(
            F.col("request_id"),
            F.col("line.id").alias(
                "line_id"
            ),
            F.col("line.name").alias(
                "line_name"
            ),
            F.col("line.modeName").alias(
                "mode_name"
            ),
            F.col(
                "line_status.id"
            ).alias(
                "status_id"
            ),
            F.col(
                "line_status.statusSeverity"
            ).alias(
                "status_severity"
            ),
            F.col(
                "line_status.statusSeverityDescription"
            ).alias(
                "status_description"
            ),
            F.col(
                "line_status.reason"
            ).alias(
                "status_reason"
            ),
            F.to_timestamp(
                F.col(
                    "line_status.created"
                )
            ).alias(
                "status_created_at"
            ),
            F.col(
                "ingested_at"
            ).alias(
                "snapshot_at"
            ),
            F.col(
                "ingestion_date"
            ),
            F.col("source"),
        )
    )

    return silver_df