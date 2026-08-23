from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import (
    ArrayType,
    BooleanType,
    StringType,
    StructField,
    StructType,
)


EVENT_SCHEMA = StructType([
    StructField("title", StringType(), True),
    StructField("date", StringType(), True),
    StructField("notes", StringType(), True),
    StructField("bunting", BooleanType(), True),
])


BANK_HOLIDAY_SCHEMA = StructType([
    StructField(
        "england-and-wales",
        StructType([
            StructField(
                "division",
                StringType(),
                True,
            ),
            StructField(
                "events",
                ArrayType(EVENT_SCHEMA),
                True,
            ),
        ]),
        True,
    ),
])


def transform_bank_holidays(
    bronze_df: DataFrame,
) -> DataFrame:

    parsed_df = (
        bronze_df
        .withColumn(
            "parsed_payload",
            F.from_json(
                F.col("payload"),
                BANK_HOLIDAY_SCHEMA,
            ),
        )
    )

    holidays_df = (
        parsed_df
        .withColumn(
            "holiday",
            F.explode(
                F.col(
                    "parsed_payload.`england-and-wales`.events"
                )
            ),
        )
        .select(
            F.col("request_id"),

            F.col(
                "parsed_payload.`england-and-wales`.division"
            ).alias("division"),

            F.col(
                "holiday.title"
            ).alias("holiday_name"),

            F.to_date(
                F.col("holiday.date"),
                "yyyy-MM-dd",
            ).alias("holiday_date"),

            F.col(
                "holiday.notes"
            ).alias("notes"),

            F.col(
                "holiday.bunting"
            ).alias("bunting"),

            F.col(
                "ingested_at"
            ).alias("snapshot_at"),

            F.col("ingestion_date"),
            F.col("source"),
        )
    )

    return holidays_df