# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "jinja2==3.1.6",
#     "typer==0.21.1",
#     "loguru==0.7.3",
#     "polars==1.37.1",
# ]
# ///

# modified from https://github.com/marimo-team/marimo-gh-pages-template/blob/main/.github/scripts/build.py

import subprocess
import jinja2
import typer
from pathlib import Path
from shutil import copytree
from loguru import logger
from pprint import pp as pprint

from metadata import CSVRecord, Records, Tag, Description, Groups
from metadata import get_description, get_metadata


def log_and_run(cmd: list[str]) -> None:
    logger.info(f"Running cmd: {cmd}")
    subprocess.run(cmd, text=True, check=True)


def export_marimo(marimo_data: dict[Tag, Records], output_dir: Path) -> None:
    def export_cmd(record: CSVRecord, mode: str) -> list[str]:
        out_mode: str = record["mode1"] if mode == "run" else record["mode2"]
        return f"uvx marimo export html-wasm --sandbox --force --mode {mode} {record['path']} -o {output_dir}/{out_mode}".split()

    for tag, records in marimo_data.items():
        for record in records:
            try:
                logger.info(f"Exporting {record['name']} to {record['mode1']}")
                log_and_run(export_cmd(record, mode="run"))

                logger.info(f"Exporting {record['name']} to {record['mode2']}")
                log_and_run(export_cmd(record, mode="edit"))

                logger.info(f"Successfully exported {record['path']}")

            except subprocess.CalledProcessError as e:
                logger.error(f"Error exporting {record['name']}")
                logger.error(f"Command Error: {e.stderr}")

            except Exception as e:
                logger.error(f"Unexpected error exporting {record['name']}: {e}")


def export_manim(manim_data: dict[Tag, Records], output_dir: Path) -> None:
    def render_cmd(record: CSVRecord, mode: str) -> list[str]:
        return f"uv run manim-slides render {record['path']}".split()

    def convert_cmd(record: CSVRecord, mode: str) -> list[str]:
        mode = "mode1" if mode == "light" else "mode2"

        config: list[str] = [
            "--offline",
            "-ccontrols=true",
            "-cprogress=true",
            f"-ctitle={record['name']}",
            Path(record["path"]).stem,
            f"_site/{record[mode]}",
        ]

        return "uv run manim-slides convert".split() + config

    for tag, records in manim_data.items():
        for record in records:
            try:
                logger.info(f"Rendering {record['name']}")
                log_and_run(render_cmd(record, mode="run"))

                logger.info(f"Exporting {record['name']} to {record['mode1']} (light)")
                log_and_run(convert_cmd(record, mode="light"))

                logger.info(f"Exporting {record['name']} to {record['mode2']} (dark)")
                log_and_run(convert_cmd(record, mode="dark"))

                logger.info(f"Successfully exported {record['path']}")

            except subprocess.CalledProcessError as e:
                logger.error(f"Error exporting {record['name']}")
                logger.error(f"Command Error: {e.stderr}")

            except Exception as e:
                logger.error(f"Unexpected error exporting {record['name']}: {e}")


def generate_index(
    output_dir: Path,
    metadata: Groups,
    description: dict[str, Description],
    template_file: Path,
) -> None:
    logger.info("Generating index.html")

    try:
        # setting up Jinja2 environment and loading template
        template = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_file.parent),
            autoescape=jinja2.select_autoescape(["html", "xml"]),
        ).get_template(template_file.name)

        logger.info("Loaded template from env, starting to render html...")

        logger.info("Arguments to template.render:")
        logger.info("----------   marimo   ----------")
        pprint(metadata["marimo"])
        logger.info("----------   manim   ----------")
        pprint(metadata["manim"])
        logger.info("--------  description   --------")
        pprint(description)

        rendered_html: str = template.render(
            m_marimo=metadata["marimo"],
            m_manim=metadata["manim"],
            description=description,
        )
        (output_dir / "index.html").write_text(rendered_html)

        copytree(Path.cwd() / "images", output_dir / "images")
        copytree(Path.cwd() / "slides", output_dir / "slides")
        open(output_dir / ".nojekyll", "w").close()  # touch .nojekyll

        logger.info(f"Successfully generated index.html at {output_dir / 'index.html'}")

    except IOError as e:
        logger.error(f"Error generating index.html: {e}")

    except jinja2.exceptions.TemplateError as e:
        logger.error(f"Error rendering template: {e}")


def main(
    output: str = "_site", template: str = ".github/scripts/tailwind.html.j2"
) -> None:
    """Main function to export marimo notebooks and manim animations.

    This function:
    1. Parses command line arguments
    2. Exports all marimo notebooks in the 'marimo' group
    3. Exports all manim animations in the 'manim' group
    4. Generates an index.html file that lists all the notebooks and animations

    Parameters:
        output: Directory where the exported files will be saved (default: _site)
        template: Path to the template file (default: templates/index.html.j2)

    Returns:
        None
    """
    logger.info("Starting marimo build process")

    output_dir: Path = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")

    # Convert template to Path if provided
    template_file: Path = Path(template)
    logger.info(f"Using template file: {template_file}")

    metadata: Groups = get_metadata()
    logger.info("Metadata: ")
    pprint(metadata)

    description: dict[str, Description] = get_description()
    logger.info("Description: ")
    pprint(description)

    export_marimo(metadata["marimo"], output_dir)
    export_manim(metadata["manim"], output_dir)

    generate_index(output_dir, metadata, description, template_file)
    logger.info(f"Build completed successfully. Output directory: {output_dir}")


if __name__ == "__main__":
    typer.run(main)
