from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def prepare_station_line_bridge(
    station_lines_df: DataFrame,
    stop_points_df: DataFrame,
    dim_station_df: DataFrame,
    dim_line_df: DataFrame,
) -> DataFrame:

    latest_station_line_snapshot = (
        station_lines_df
        .agg(
            F.max("snapshot_at").alias(
                "latest_snapshot"
            )
        )
        .first()["latest_snapshot"]
    )

    if latest_station_line_snapshot is None:
        raise ValueError(
            "No station-line relationships found."
        )

    latest_station_lines_df = (
        station_lines_df
        .filter(
            F.col("snapshot_at")
            == latest_station_line_snapshot
        )
        .select(
            "stop_point_id",
            "line_id",
            "line_name",
            "snapshot_at",
        )
        .dropDuplicates([
            "stop_point_id",
            "line_id",
        ])
    )

    latest_stop_point_snapshot = (
        stop_points_df
        .agg(
            F.max("snapshot_at").alias(
                "latest_snapshot"
            )
        )
        .first()["latest_snapshot"]
    )

    if latest_stop_point_snapshot is None:
        raise ValueError(
            "No stop-point reference data found."
        )

    stop_point_lookup_df = (
        stop_points_df
        .filter(
            F.col("snapshot_at")
            == latest_stop_point_snapshot
        )
        .filter(
            F.col("station_naptan").isNotNull()
        )
        .select(
            "stop_point_id",
            F.col(
                "station_naptan"
            ).alias(
                "station_id"
            ),
        )
        .dropDuplicates()
    )

    current_line_ids_df = (
        dim_line_df
        .filter(
            F.col("is_current")
        )
        .select("line_id")
        .distinct()
    )


    relationships_df = (
        latest_station_lines_df.alias("rel")
        .join(
            stop_point_lookup_df.alias("lookup"),
            on="stop_point_id",
            how="inner",
        )
        .select(
            F.col("lookup.station_id"),
            F.col("rel.line_id"),
            F.col("rel.snapshot_at"),
        )

        # Keep only lines represented by
        # the UrbanPulse Tube line dimension.
        .join(
            current_line_ids_df,
            on="line_id",
            how="inner",
        )

        .dropDuplicates([
            "station_id",
            "line_id",
        ])
    )

    current_station_df = (
        dim_station_df
        .filter(
            F.col("is_current")
        )
        .select(
            "station_key",
            "station_id",
        )
    )

    current_line_df = (
        dim_line_df
        .filter(
            F.col("is_current")
        )
        .select(
            "line_key",
            "line_id",
        )
    )

    return (
        relationships_df.alias("rel")
        .join(
            current_station_df.alias("station"),
            on="station_id",
            how="inner",
        )
        .join(
            current_line_df.alias("line"),
            on="line_id",
            how="inner",
        )
        .select(
            F.col("station.station_key"),
            F.col("line.line_key"),
            F.col("rel.station_id"),
            F.col("rel.line_id"),
            F.col(
                "rel.snapshot_at"
            ).alias(
                "source_snapshot_at"
            ),
        )
    )