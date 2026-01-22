# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "polars==1.37.1",
#     "loguru==0.7.0",
# ]
# ///

from typing import TypedDict, Literal
from pathlib import Path
import polars


class CSVRecord(TypedDict):
    name: str
    tag: str
    year: int
    path: str
    description: str


Records = list[CSVRecord]
Tag = str
Group = Literal["manim", "marimo", "hidden", "python"]


def get_metadata() -> dict[Group, dict[Tag, Records]]:
    df = polars.read_csv(".github/metadata.csv").group_by("tag", maintain_order=True)
    desc: dict[Tag, dict[str, str]] = get_description(".github/tags.csv")
    metadata: dict[Group, dict[Tag, Records]] = {
        "marimo": {},
        "manim": {},
        "python": {},
        "hidden": {},
    }

    for (tag, *_), content in df:
        group = desc[tag]["group"]  # get 'group' of tag
        metadata[group][tag] = content.to_dicts()  # type: ignore

    return metadata


def get_description(path) -> dict[Tag, dict[str, str]]:
    df: polars.DataFrame = polars.read_csv(path)
    return df.rows_by_key("tag", named=True, unique=True)
