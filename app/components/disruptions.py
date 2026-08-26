import re

import pandas as pd

from dash import html


def clean_reason(
    reason,
    line_name=None,
):
    if (
        reason is None
        or pd.isna(reason)
        or not str(reason).strip()
    ):
        return None

    text = str(reason).strip()

    # Remove prefixes such as:
    # "PICCADILLY LINE:"
    if line_name:
        prefix_pattern = (
            rf"^{re.escape(str(line_name))}"
            r"(?:\s+LINE)?:\s*"
        )

        text = re.sub(
            prefix_pattern,
            "",
            text,
            flags=re.IGNORECASE,
        )

    else:
        text = re.sub(
            r"^[A-Z '&-]+\s+LINE:\s*",
            "",
            text,
        )

    return text.strip()


def split_reason(
    reason,
    line_name=None,
):
    text = clean_reason(
        reason,
        line_name,
    )

    if not text:
        return []

    return [
        sentence.strip()
        for sentence in re.split(
            r"(?<=[.!?])\s+",
            text,
        )
        if sentence.strip()
    ]


def build_reason_content(
    reason,
    line_name=None,
    expandable=True,
):
    sentences = split_reason(
        reason,
        line_name,
    )

    if not sentences:
        return html.Span(
            "No additional information",
            className="text-secondary",
        )

    primary = sentences[0]
    remaining = sentences[1:]

    children = [
        html.Div(
            primary,
            className="reason-primary",
        )
    ]

    if remaining:

        details_content = html.Ul(
            [
                html.Li(sentence)
                for sentence in remaining
            ],
            className="reason-list",
        )

        if expandable:
            children.append(
                html.Details(
                    [
                        html.Summary(
                            "More details",
                            className=(
                                "reason-summary"
                            ),
                        ),
                        details_content,
                    ],
                    className="mt-2",
                )
            )

        else:
            children.append(
                details_content
            )

    return html.Div(children)