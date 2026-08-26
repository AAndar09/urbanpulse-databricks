import pandas as pd


def format_timestamp(value):
    if value is None or pd.isna(value):
        return "No data"

    return (
        pd.to_datetime(value)
        .strftime(
            "%d %b %Y, %H:%M"
        )
    )


def format_date(value):
    if value is None or pd.isna(value):
        return "No data"

    return (
        pd.to_datetime(value)
        .strftime(
            "%d %b %Y"
        )
    )


def format_eta(seconds):
    if (
        seconds is None
        or pd.isna(seconds)
    ):
        return "No data"

    return (
        f"{float(seconds) / 60:.1f} min"
    )