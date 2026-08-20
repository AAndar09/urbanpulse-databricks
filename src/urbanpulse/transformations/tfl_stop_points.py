from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import (
    ArrayType,
    DoubleType,
    StringType,
    StructField,
    StructType,
)


LINE_SCHEMA = StructType([
    StructField("id", StringType(), True),
    StructField("name", StringType(), True),
])


STOP_POINT_SCHEMA = StructType([
    StructField(
        "stopPoints",
        ArrayType(
            StructType([
                StructField(
                    "id",
                    StringType(),
                    True,
                ),
                StructField(
                    "commonName",
                    StringType(),
                    True,
                ),
                StructField(
                    "stopType",
                    StringType(),
                    True,
                ),
                StructField(
                    "stationNaptan",
                    StringType(),
                    True,
                ),
                StructField(
                    "lat",
                    DoubleType(),
                    True,
                ),
                StructField(
                    "lon",
                    DoubleType(),
                    True,
                ),
                StructField(
                    "modes",
                    ArrayType(
                        StringType()
                    ),
                    True,
                ),
                StructField(
                    "lines",
                    ArrayType(
                        LINE_SCHEMA
                    ),
                    True,
                ),
            ])
        ),
        True,
    )
])


def parse_tfl_stop_points(
    bronze_df: DataFrame,
) -> DataFrame:

    return (
        bronze_df
        .withColumn(
            "parsed_payload",
            F.from_json(
                F.col("payload"),
                STOP_POINT_SCHEMA,
            ),
        )
        .withColumn(
            "stop_point",
            F.explode_outer(
                F.col(
                    "parsed_payload.stopPoints"
                )
            ),
        )
    )


def transform_stop_points(
    parsed_df: DataFrame,
) -> DataFrame:

    return (
        parsed_df
        .select(
            F.col("request_id"),

            F.col(
                "stop_point.id"
            ).alias(
                "stop_point_id"
            ),

            F.col(
                "stop_point.stationNaptan"
            ).alias(
                "station_naptan"
            ),

            F.col(
                "stop_point.commonName"
            ).alias(
                "common_name"
            ),

            F.col(
                "stop_point.stopType"
            ).alias(
                "stop_type"
            ),

            F.col(
                "stop_point.lat"
            ).alias(
                "latitude"
            ),

            F.col(
                "stop_point.lon"
            ).alias(
                "longitude"
            ),

            F.col(
                "stop_point.modes"
            ).alias(
                "modes"
            ),

            F.col(
                "ingested_at"
            ).alias(
                "snapshot_at"
            ),

            F.col("ingestion_date"),
            F.col("source"),
        )
    )


def transform_stop_point_lines(
    parsed_df: DataFrame,
) -> DataFrame:

    return (
        parsed_df
        .withColumn(
            "line",
            F.explode_outer(
                F.col(
                    "stop_point.lines"
                )
            ),
        )
        .select(
            F.col("request_id"),

            F.col(
                "stop_point.id"
            ).alias(
                "stop_point_id"
            ),

            F.col(
                "line.id"
            ).alias(
                "line_id"
            ),

            F.col(
                "line.name"
            ).alias(
                "line_name"
            ),

            F.col(
                "ingested_at"
            ).alias(
                "snapshot_at"
            ),

            F.col("ingestion_date"),
            F.col("source"),
        )
    )