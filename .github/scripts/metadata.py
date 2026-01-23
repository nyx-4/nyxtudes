# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "polars==1.37.1",
#     "loguru==0.7.3",
# ]
# ///

from typing import TypedDict
from pathlib import Path

import polars
from loguru import logger


class CSVRecord(TypedDict):
    name: str
    tag: str
    year: int
    path: str
    description: str
    mode1: str
    mode2: str
    thumbnail: str


Records = list[CSVRecord]
Tag = str
Description = dict[str, str]


class Groups(TypedDict):
    marimo: dict[Tag, Records]
    manim: dict[Tag, Records]
    python: dict[Tag, Records]
    hidden: dict[Tag, Records]


def get_metadata() -> Groups:
    df = polars.read_csv(".github/metadata.csv").group_by("tag")
    desc: dict[Tag, Description] = get_description()
    metadata: Groups = {
        "marimo": {},
        "manim": {},
        "python": {},
        "hidden": {},
    }

    for (tag, *_), content in df:
        group = desc[tag]["group"]  # get 'group' of tag

        def f_mode1(path: str) -> str:  # app for marimo, light for manim
            mode: str = "app" if group == "marimo" else "light"
            return f"{tag}/{mode}/" + Path(path).with_suffix(".html").name

        def f_mode2(path) -> str:  # notebook for marimo, dark for manim
            mode: str = "notebook" if group == "marimo" else "dark"
            return f"{tag}/{mode}/" + Path(path).with_suffix(".html").name

        def f_image(path) -> str:
            images: list[Path] = list(Path("images/").glob(Path(path).stem + ".*"))
            fallback_image = "https://avatars.githubusercontent.com/u/219992970"

            if len(images) == 0:
                return fallback_image  # if no image found
            elif len(images) == 1:
                return str(images[0])
            else:
                logger.warning(f"multiple images found for {path}: {images}")
                return str(images[0])

        # add three new columns (mode1, mode2, and thumbnail) in metadata
        # which are only used by manim and marimo groups for index.html
        metadata[group][tag] = content.with_columns(
            polars.col("path").map_elements(f_mode1, polars.String).alias("mode1"),
            polars.col("path").map_elements(f_mode2, polars.String).alias("mode2"),
            polars.col("path").map_elements(f_image, polars.String).alias("thumbnail"),
        ).to_dicts()

    return metadata


def get_description() -> dict[Tag, Description]:
    df: polars.DataFrame = polars.read_csv(".github/tags.csv")
    return df.rows_by_key("tag", named=True, unique=True)
