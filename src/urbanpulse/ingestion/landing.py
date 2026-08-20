import json
from datetime import datetime, timezone
from pathlib import Path


def land_json(
    payload,
    base_path: str,
    source: str,
    dataset: str,
    request_id: str,
) -> str:

    now = datetime.now(timezone.utc)

    directory = (
        Path(base_path)
        / source
        / dataset
        / now.strftime("%Y")
        / now.strftime("%m")
        / now.strftime("%d")
        / now.strftime("%H")
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path = (
        directory
        / f"{request_id}.json"
    )

    with file_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            ensure_ascii=False,
        )

    return str(file_path)