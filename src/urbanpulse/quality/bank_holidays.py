from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def valid_bank_holidays(
    df: DataFrame,
) -> DataFrame:

    return (
        df
        .filter(
            F.col("request_id").isNotNull()
        )
        .filter(
            F.col("division").isNotNull()
        )
        .filter(
            F.col("holiday_name").isNotNull()
        )
        .filter(
            F.col("holiday_date").isNotNull()
        )
        .filter(
            F.col("snapshot_at").isNotNull()
        )
    )


def invalid_bank_holidays(
    df: DataFrame,
) -> DataFrame:

    valid_df = valid_bank_holidays(df)

    return df.join(
        valid_df.select(
            "request_id",
            "holiday_name",
            "holiday_date",
        ),
        on=[
            "request_id",
            "holiday_name",
            "holiday_date",
        ],
        how="left_anti",
    )