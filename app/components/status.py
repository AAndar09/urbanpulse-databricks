def get_service_style(status_description):
    status = (
        str(status_description or "")
        .strip()
        .lower()
    )

    if status == "good service":
        return {
            "label": "Good Service",
            "color": "success",
        }

    warning_terms = (
        "minor delays",
        "part closure",
        "planned closure",
        "special service",
        "reduced service",
    )

    if any(
        term in status
        for term in warning_terms
    ):
        return {
            "label": status_description,
            "color": "warning",
        }

    danger_terms = (
        "severe delays",
        "suspended",
        "closed",
        "service closed",
        "part suspended",
    )

    if any(
        term in status
        for term in danger_terms
    ):
        return {
            "label": status_description,
            "color": "danger",
        }

    return {
        "label": (
            status_description
            or "Unknown"
        ),
        "color": "secondary",
    }