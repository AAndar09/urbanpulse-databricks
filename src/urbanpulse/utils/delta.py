from delta.tables import DeltaTable
from pyspark.sql import DataFrame, SparkSession


def merge_insert_only(
    spark: SparkSession,
    source_df: DataFrame,
    target_table: str,
    merge_condition: str,
) -> str:

    if not spark.catalog.tableExists(
        target_table
    ):
        (
            source_df
            .write
            .format("delta")
            .mode("overwrite")
            .saveAsTable(
                target_table
            )
        )

        return "created"

    target = DeltaTable.forName(
        spark,
        target_table,
    )

    (
        target.alias("target")
        .merge(
            source_df.alias("source"),
            merge_condition,
        )
        .whenNotMatchedInsertAll()
        .execute()
    )

    return "merged"


def merge_upsert(
    spark: SparkSession,
    source_df: DataFrame,
    target_table: str,
    merge_condition: str,
    ) -> str:

    if not spark.catalog.tableExists(
        target_table
    ):
        (
            source_df
            .write
            .format("delta")
            .mode("overwrite")
            .saveAsTable(
                target_table
            )
        )

        return "created"

    target = DeltaTable.forName(
        spark,
        target_table,
    )

    (
        target.alias("target")
        .merge(
            source_df.alias("source"),
            merge_condition,
        )
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )

    return "upserted"