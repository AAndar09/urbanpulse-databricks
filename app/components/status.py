def get_service_style(
    status_severity,
    status_description=None,
):
    try:
        severity = int(
            status_severity
        )

    except (
        TypeError,
        ValueError,
    ):
        severity = None


    # TfL severity based classification

    if severity == 10:
        return {
            "label": "Healthy",
            "color": "success",
        }

    if severity in {
        7,
        8,
        9,
    }:
        return {
            "label": "Degraded",
            "color": "warning",
        }

    if severity in {
        1,
        2,
        3,
        4,
        5,
        6,
    }:
        return {
            "label": "Disrupted",
            "color": "danger",
        }


    # Description fallback

    status = (
        str(
            status_description
            or ""
        )
        .strip()
        .lower()
    )

    if status == "good service":
        return {
            "label": "Healthy",
            "color": "success",
        }

    warning_terms = (
        "minor delays",
        "reduced service",
        "bus service",
        "special service",
    )

    if any(
        term in status
        for term in warning_terms
    ):
        return {
            "label": "Degraded",
            "color": "warning",
        }

    danger_terms = (
        "severe delays",
        "suspended",
        "closure",
        "closed",
    )

    if any(
        term in status
        for term in danger_terms
    ):
        return {
            "label": "Disrupted",
            "color": "danger",
        }

    return {
        "label": "Unknown",
        "color": "secondary",
    }