import pandas as pd
import streamlit as st

from services.queries import (
    get_current_line_status,
    get_latest_arrival_kpis,
    get_latest_weather_kpis,
    get_network_summary,
    get_recent_network_trends,
)


st.set_page_config(
    page_title="UrbanPulse",
    page_icon="🚇",
    layout="wide",
)


def get_value(
    dataframe,
    column,
    default=None,
):
    if dataframe.empty:
        return default

    value = dataframe.iloc[0][column]

    if pd.isna(value):
        return default

    return value


st.title("UrbanPulse")

st.caption(
    "London Urban Mobility Intelligence Platform"
)

st.subheader("Network Overview")


try:

    network_df = get_network_summary()

    arrival_df = get_latest_arrival_kpis()

    weather_df = get_latest_weather_kpis()

    line_status_df = get_current_line_status()

    trends_df = get_recent_network_trends()


    # -------------------------
    # Network KPIs
    # -------------------------

    total_lines = int(
        get_value(
            network_df,
            "total_lines",
            0,
        )
    )

    good_lines = int(
        get_value(
            network_df,
            "good_service_lines",
            0,
        )
    )

    disrupted_lines = int(
        get_value(
            network_df,
            "disrupted_lines",
            0,
        )
    )

    good_pct = float(
        get_value(
            network_df,
            "good_service_pct",
            0,
        )
    )


    st.markdown("### Network Health")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Tube Lines",
        total_lines,
    )

    col2.metric(
        "Good Service",
        good_lines,
    )

    col3.metric(
        "Disrupted",
        disrupted_lines,
    )

    col4.metric(
        "Good Service %",
        f"{good_pct:.1f}%",
    )


    # -------------------------
    # Arrival and weather KPIs
    # -------------------------

    arrival_observations = int(
        get_value(
            arrival_df,
            "arrival_observations",
            0,
        )
    )

    stations_observed = int(
        get_value(
            arrival_df,
            "stations_observed",
            0,
        )
    )

    avg_eta_seconds = get_value(
        arrival_df,
        "avg_eta_seconds",
    )

    temperature_c = get_value(
        weather_df,
        "avg_temperature_c",
    )


    st.markdown("### Operational Activity")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Arrival Observations",
        arrival_observations,
    )

    col2.metric(
        "Stations Observed",
        stations_observed,
    )

    if avg_eta_seconds is not None:

        col3.metric(
            "Average ETA",
            f"{avg_eta_seconds / 60:.1f} min",
        )

    else:

        col3.metric(
            "Average ETA",
            "No data",
        )


    if temperature_c is not None:

        col4.metric(
            "Temperature",
            f"{temperature_c:.1f} °C",
        )

    else:

        col4.metric(
            "Temperature",
            "No data",
        )


    # -------------------------
    # Current line status
    # -------------------------

    st.markdown("### Current Tube Status")


    display_status_df = (
        line_status_df.copy()
    )

    display_status_df[
        "service_state"
    ] = display_status_df[
        "is_disrupted"
    ].apply(
        lambda value:
            "Disrupted"
            if value
            else "Good Service"
    )


    status_columns = [
        "line_name",
        "status_description",
        "service_state",
        "status_snapshot_at_local",
    ]


    st.dataframe(
        display_status_df[
            status_columns
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "line_name":
                "Line",

            "status_description":
                "Status",

            "service_state":
                "Service State",

            "status_snapshot_at_local":
                "Last Updated",
        },
    )


    # -------------------------
    # Disruptions
    # -------------------------

    st.markdown("### Current Disruptions")


    disruption_df = (
        line_status_df[
            line_status_df[
                "is_disrupted"
            ] == True
        ]
    )


    if disruption_df.empty:

        st.success(
            "No current Tube disruptions."
        )

    else:

        st.dataframe(
            disruption_df[
                [
                    "line_name",
                    "status_description",
                    "status_reason",
                    "status_snapshot_at_local",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "line_name":
                    "Line",

                "status_description":
                    "Status",

                "status_reason":
                    "Reason",

                "status_snapshot_at_local":
                    "Last Updated",
            },
        )


    # -------------------------
    # Trends
    # -------------------------

    st.markdown("### Recent Trends")


    if not trends_df.empty:

        trends_df = (
            trends_df
            .sort_values(
                "calendar_date"
            )
        )


        col1, col2 = st.columns(2)


        with col1:

            st.markdown(
                "#### Disruption Rate"
            )

            disruption_trend = (
                trends_df[
                    [
                        "calendar_date",
                        "disruption_rate_pct",
                    ]
                ]
                .dropna()
                .set_index(
                    "calendar_date"
                )
            )

            if not disruption_trend.empty:

                st.line_chart(
                    disruption_trend
                )

            else:

                st.info(
                    "No disruption trend data available."
                )


        with col2:

            st.markdown(
                "#### Arrival Activity"
            )

            arrival_trend = (
                trends_df[
                    [
                        "calendar_date",
                        "arrival_observations",
                    ]
                ]
                .set_index(
                    "calendar_date"
                )
            )

            st.line_chart(
                arrival_trend
            )

    else:

        st.info(
            "No historical trend data available."
        )


    # -------------------------
    # Freshness
    # -------------------------

    st.markdown("### Data Freshness")


    latest_line_update = (
        line_status_df[
            "status_snapshot_at_local"
        ].max()
        if not line_status_df.empty
        else None
    )

    arrival_date = get_value(
        arrival_df,
        "calendar_date",
    )

    weather_date = get_value(
        weather_df,
        "calendar_date",
    )


    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Latest Line Status",
        (
            str(latest_line_update)
            if latest_line_update
            is not None
            else "No data"
        ),
    )

    col2.metric(
        "Latest Arrival Date",
        (
            str(arrival_date)
            if arrival_date
            is not None
            else "No data"
        ),
    )

    col3.metric(
        "Latest Weather Date",
        (
            str(weather_date)
            if weather_date
            is not None
            else "No data"
        ),
    )


except Exception as exc:

    st.error(
        "Unable to load UrbanPulse dashboard data."
    )

    st.exception(exc)