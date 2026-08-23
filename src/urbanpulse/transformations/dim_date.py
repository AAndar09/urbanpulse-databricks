from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


def generate_date_dimension(
    spark: SparkSession,
    start_date: str,
    end_date: str,
) -> DataFrame:

    date_df = spark.sql(
        f"""
        SELECT EXPLODE(
            SEQUENCE(
                TO_DATE('{start_date}'),
                TO_DATE('{end_date}'),
                INTERVAL 1 DAY
            )
        ) AS calendar_date
        """
    )

    return (
        date_df
        .withColumn(
            "date_key",
            F.date_format(
                "calendar_date",
                "yyyyMMdd",
            ).cast("int"),
        )
        .withColumn(
            "year",
            F.year("calendar_date"),
        )
        .withColumn(
            "quarter",
            F.quarter("calendar_date"),
        )
        .withColumn(
            "month",
            F.month("calendar_date"),
        )
        .withColumn(
            "month_name",
            F.date_format(
                "calendar_date",
                "MMMM",
            ),
        )
        .withColumn(
            "week_of_year",
            F.weekofyear(
                "calendar_date"
            ),
        )
        .withColumn(
            "day_of_month",
            F.dayofmonth(
                "calendar_date"
            ),
        )
        .withColumn(
            "day_of_week",
            (
                F.pmod(
                    F.dayofweek(
                        "calendar_date"
                    ) + F.lit(5),
                    F.lit(7),
                )
                + F.lit(1)
            ).cast("int"),
        )
        .withColumn(
            "day_name",
            F.date_format(
                "calendar_date",
                "EEEE",
            ),
        )
        .withColumn(
            "is_weekend",
            F.dayofweek(
                "calendar_date"
            ).isin(1, 7),
        )
    )


def enrich_with_bank_holidays(
    date_df: DataFrame,
    holidays_df: DataFrame,
) -> DataFrame:

    holiday_by_date_df = (
        holidays_df
        .groupBy("holiday_date")
        .agg(
            F.concat_ws(
                " | ",
                F.sort_array(
                    F.collect_set(
                        "holiday_name"
                    )
                ),
            ).alias(
                "holiday_name"
            )
        )
    )

    return (
        date_df
        .join(
            holiday_by_date_df,
            date_df.calendar_date
            == holiday_by_date_df.holiday_date,
            "left",
        )
        .drop("holiday_date")
        .withColumn(
            "is_bank_holiday",
            F.col(
                "holiday_name"
            ).isNotNull(),
        )
    )