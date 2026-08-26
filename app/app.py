import streamlit as st

from services.queries import (
    get_current_line_status,
)


st.set_page_config(
    page_title="UrbanPulse",
    page_icon="🚇",
    layout="wide",
)


st.title("UrbanPulse")

st.caption(
    "London Urban Mobility Intelligence Platform"
)


st.subheader("Current Tube Line Status")


try:

    line_status_df = (
        get_current_line_status()
    )

    st.success(
        "Connected to Databricks successfully."
    )

    st.dataframe(
        line_status_df,
        use_container_width=True,
        hide_index=True,
    )

except Exception as exc:

    st.error(
        "Unable to load UrbanPulse data."
    )

    st.exception(exc)