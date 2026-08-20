import json
from datetime import datetime, timezone

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    DateType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)


BRONZE_SCHEMA = StructType([
    StructField(
        "request_id",
        StringType(),
        False,
    ),
    StructField(
        "source",
        StringType(),
        False,
    ),
    StructField(
        "dataset",
        StringType(),
        False,
    ),
    StructField(
        "source_endpoint",
        StringType(),
        False,
    ),
    StructField(
        "ingested_at",
        TimestampType(),
        False,
    ),
    StructField(
        "ingestion_date",
        DateType(),
        False,
    ),
    StructField(
        "http_status",
        IntegerType(),
        True,
    ),
    StructField(
        "payload",
        StringType(),
        False,
    ),
])


def write_raw_bronze(
    spark: SparkSession,
    payload,
    request_id: str,
    source: str,
    dataset: str,
    source_endpoint: str,
    http_status: int,
    table_name: str,
) -> None:

    ingested_at = datetime.now(
        timezone.utc
    )

    rows = [{
        "request_id": request_id,
        "source": source,
        "dataset": dataset,
        "source_endpoint": source_endpoint,
        "ingested_at": ingested_at,
        "ingestion_date": (
            ingested_at.date()
        ),
        "http_status": http_status,
        "payload": json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    }]

    df = spark.createDataFrame(
        rows,
        schema=BRONZE_SCHEMA,
    )

    (
        df.write
        .format("delta")
        .mode("append")
        .saveAsTable(table_name)
    )