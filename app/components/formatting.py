import pandas as pd


def format_timestamp(value):

    if value is None or pd.isna(value):
        return "No data"

    timestamp = pd.to_datetime(value)

    return timestamp.strftime(
        "%d %b %Y, %H:%M"
    )