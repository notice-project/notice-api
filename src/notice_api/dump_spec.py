import json
from pathlib import Path
from typing import Literal

import click
import yaml

from notice_api.main import app


def get_format(ctx: click.Context, _option: click.Option, value: str | None):
    """Get the format from the output file extension."""

    if value == "yml":
        return "yaml"
    if value is not None:
        return value

    output: Path = ctx.params["output"]
    match output:
        case Path(suffix=".json"):
            return "json"
        case Path(suffix=".yaml" | ".yml"):
            return "yaml"
        case _:
            raise click.BadParameter(
                f"Could not determine format from output file extension: {output.suffix}"
            )


@click.command
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    default="openapi.yaml",
    callback=lambda _ctx, _option, value: Path(value),
    help="Output file",
)
@click.option(
    "-f",
    "--format",
    type=click.Choice(["json", "yaml"]),
    callback=get_format,
    help="Output format (respective to file extension)",
)
def dump_spec(output: Path, format: Literal["json", "yaml"]):
    """Dump the OpenAPI specification to a file."""

    spec = app.openapi()

    if format == "json":
        with output.open("w") as f:
            json.dump(spec, f)
    elif format == "yaml":
        with output.open("w") as f:
            yaml.dump(spec, f)


if __name__ == "__main__":
    dump_spec()
