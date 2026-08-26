import streamlit as st


st.set_page_config(
    page_title="UrbanPulse",
    page_icon="🚇",
    layout="wide",
)


pages = [
    st.Page(
        "pages/network_overview.py",
        title="Network Overview",
        icon="🏙️",
        default=True,
    ),

    st.Page(
        "pages/line_status.py",
        title="Line Status",
        icon="🚇",
    ),
]


navigation = st.navigation(
    pages
)

navigation.run()