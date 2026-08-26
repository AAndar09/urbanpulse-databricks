import streamlit as st

from components.formatting import (
    format_timestamp,
)

from services.queries import (
    get_current_line_status,
)


st.title("Line Status")

st.caption(
    "Current operational status of London Underground lines"
)


try:

    status_df = (
        get_current_line_status()
    )


    # -------------------------
    # Prepare display fields
    # -------------------------

    status_df[
        "service_state"
    ] = status_df[
        "is_disrupted"
    ].apply(
        lambda value:
            "Disrupted"
            if value
            else "Good Service"
    )


    status_df[
        "last_updated"
    ] = status_df[
        "status_snapshot_at_local"
    ].apply(
        format_timestamp
    )


    # -------------------------
    # Filters
    # -------------------------

    st.markdown("### Filters")

    col1, col2 = st.columns(2)


    line_options = (
        ["All"]
        +
        sorted(
            status_df[
                "line_name"
            ]
            .dropna()
            .unique()
            .tolist()
        )
    )


    selected_line = (
        col1.selectbox(
            "Tube Line",
            line_options,
        )
    )


    selected_state = (
        col2.selectbox(
            "Service State",
            [
                "All",
                "Good Service",
                "Disrupted",
            ],
        )
    )


    # -------------------------
    # Apply filters
    # -------------------------

    filtered_df = (
        status_df.copy()
    )


    if selected_line != "All":

        filtered_df = (
            filtered_df[
                filtered_df[
                    "line_name"
                ]
                ==
                selected_line
            ]
        )


    if selected_state != "All":

        filtered_df = (
            filtered_df[
                filtered_df[
                    "service_state"
                ]
                ==
                selected_state
            ]
        )


    # -------------------------
    # KPI cards
    # -------------------------

    total_lines = len(
        filtered_df
    )

    good_lines = (
        filtered_df[
            "is_good_service"
        ].sum()
    )

    disrupted_lines = (
        filtered_df[
            "is_disrupted"
        ].sum()
    )


    st.markdown("### Service Summary")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Lines Shown",
        int(total_lines),
    )

    col2.metric(
        "Good Service",
        int(good_lines),
    )

    col3.metric(
        "Disrupted",
        int(disrupted_lines),
    )


    # -------------------------
    # Status table
    # -------------------------

    st.markdown("### Current Status")


    if filtered_df.empty:

        st.info(
            "No lines match the selected filters."
        )

    else:

        display_df = (
            filtered_df[
                [
                    "line_name",
                    "service_state",
                    "status_description",
                    "status_reason",
                    "last_updated",
                ]
            ]
            .copy()
        )


        display_df[
            "status_reason"
        ] = display_df[
            "status_reason"
        ].fillna(
            "No additional information"
        )


        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "line_name":
                    "Line",

                "service_state":
                    "Service State",

                "status_description":
                    "Status",

                "status_reason":
                    "Reason",

                "last_updated":
                    "Last Updated",
            },
        )


except Exception as exc:

    st.error(
        "Unable to load Tube line status."
    )

    st.exception(exc)