from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import (
    ArrayType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)


ARRIVAL_SCHEMA = ArrayType(
    StructType([
        StructField("id", StringType(), True),
        StructField("operationType", IntegerType(), True),
        StructField("vehicleId", StringType(), True),
        StructField("naptanId", StringType(), True),
        StructField("stationName", StringType(), True),
        StructField("lineId", StringType(), True),
        StructField("lineName", StringType(), True),
        StructField("platformName", StringType(), True),
        StructField("direction", StringType(), True),
        StructField("bearing", StringType(), True),
        StructField("destinationNaptanId", StringType(), True),
        StructField("destinationName", StringType(), True),
        StructField("timestamp", StringType(), True),
        StructField("timeToStation", IntegerType(), True),
        StructField("currentLocation", StringType(), True),
        StructField("towards", StringType(), True),
        StructField("expectedArrival", StringType(), True),
        StructField("timeToLive", StringType(), True),
        StructField("modeName", StringType(), True),
    ])
)


def transform_tfl_arrivals(
    bronze_df: DataFrame,
) -> DataFrame:

    parsed_df = (
        bronze_df
        .withColumn(
            "parsed_payload",
            F.from_json(
                F.col("payload"),
                ARRIVAL_SCHEMA,
            ),
        )
        .withColumn(
            "arrival",
            F.explode(
                F.col("parsed_payload")
            ),
        )
    )

    silver_df = (
        parsed_df
        .select(
            F.col("request_id"),

            F.regexp_extract(
                F.col("source_endpoint"),
                r"/StopPoint/([^/]+)/Arrivals",
                1,
            ).alias(
                "requested_stop_point_id"
            ),

            F.col(
                "arrival.id"
            ).alias(
                "arrival_id"
            ),

            F.col(
                "arrival.vehicleId"
            ).alias(
                "vehicle_id"
            ),

            F.col(
                "arrival.naptanId"
            ).alias(
                "naptan_id"
            ),

            F.col(
                "arrival.stationName"
            ).alias(
                "station_name"
            ),

            F.col(
                "arrival.lineId"
            ).alias(
                "line_id"
            ),

            F.col(
                "arrival.lineName"
            ).alias(
                "line_name"
            ),

            F.col(
                "arrival.platformName"
            ).alias(
                "platform_name"
            ),

            F.col(
                "arrival.direction"
            ).alias(
                "direction"
            ),

            F.col(
                "arrival.destinationNaptanId"
            ).alias(
                "destination_naptan_id"
            ),

            F.col(
                "arrival.destinationName"
            ).alias(
                "destination_name"
            ),

            F.to_timestamp(
                F.col("arrival.timestamp")
            ).alias(
                "prediction_timestamp"
            ),

            F.col(
                "arrival.timeToStation"
            ).alias(
                "time_to_station_seconds"
            ),

            F.col(
                "arrival.currentLocation"
            ).alias(
                "current_location"
            ),

            F.col(
                "arrival.towards"
            ).alias(
                "towards"
            ),

            F.to_timestamp(
                F.col(
                    "arrival.expectedArrival"
                )
            ).alias(
                "expected_arrival"
            ),

            F.to_timestamp(
                F.col(
                    "arrival.timeToLive"
                )
            ).alias(
                "prediction_expires_at"
            ),

            F.col(
                "arrival.modeName"
            ).alias(
                "mode_name"
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