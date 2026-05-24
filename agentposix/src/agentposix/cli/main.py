import json

import click
from rich.console import Console
from rich.tree import Tree

from agentposix.core.freeze import freeze as freeze_aso
from agentposix.core.resume import resume as resume_aso
from agentposix.models.aso import AgentStateObject
from agentposix.storage.filesystem import FilesystemBackend

console = Console()


@click.group(help="Agent POSIX CLI")
def app():
    """Agent POSIX CLI."""


@app.command()
@click.argument("session_id")
@click.option("--path", default=".agentposix", show_default=True)
def inspect(session_id: str, path: str):
    """Inspect an Agent State Object (ASO)."""
    try:
        backend = FilesystemBackend(path)
        aso = backend.read_aso(session_id)
        tree = Tree(f"[bold blue]ASO: {session_id}[/bold blue]")
        tree.add(f"Status: [bold]{aso.status.value}[/bold]")
        tree.add(f"Node: {aso.execution_pointer.current_node_id}")
        se_branch = tree.add("Side Effects")
        for se in aso.side_effects.entries:
            color = "green" if se.result_summary else "yellow"
            se_branch.add(
                f"{se.tool_name} [[bold {color}]{se.idempotency_key[:8]}[/bold {color}]]"
            )
        console.print(tree)
    except Exception as e:
        console.print(f"[bold red]Error loading ASO:[/bold red] {str(e)}")
        raise SystemExit(1)


@app.command()
@click.argument("session_id")
@click.option("--path", default=".agentposix", show_default=True)
def resume(session_id: str, path: str):
    """Resume an Agent State Object (ASO)."""
    try:
        backend = FilesystemBackend(path)
        aso = resume_aso(session_id, backend)
        tree = Tree(f"[bold blue]Resumed ASO: {session_id}[/bold blue]")
        tree.add(f"Status: [bold]{aso.status.value}[/bold]")
        tree.add(f"Frozen At: {aso.frozen_at or 'unknown'}")
        tree.add(f"Resumed At: {aso.resumed_at or 'unknown'}")
        tree.add("Checksum: [bold green]valid[/bold green]")
        if aso.extensions.get("resume_advisories"):
            advisories = tree.add("Advisories")
            for advisory in aso.extensions["resume_advisories"]:
                advisories.add(str(advisory))
        console.print(tree)
    except Exception as e:
        console.print(f"[bold red]Error resuming ASO:[/bold red] {str(e)}")
        raise SystemExit(1)


@app.command()
@click.option(
    "--input",
    "input_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to a complete ASO JSON payload. This command is intended for debugging.",
)
@click.option("--path", default=".agentposix", show_default=True)
@click.option("--summary", default="", help="Optional checkpoint summary override.")
def freeze(input_path: str, path: str, summary: str):
    """Create a manual checkpoint from an ASO JSON payload."""
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        aso = AgentStateObject.model_validate(payload)
        backend = FilesystemBackend(path)
        frozen = freeze_aso(aso, backend, summary=summary)

        tree = Tree(f"[bold blue]Frozen ASO: {frozen.identity.session_id}[/bold blue]")
        tree.add(f"Status: [bold]{frozen.status.value}[/bold]")
        tree.add(f"Frozen At: {frozen.frozen_at or 'unknown'}")
        tree.add(f"Checksum: {frozen.checksum or 'missing'}")
        if frozen.human_summary:
            tree.add(f"Summary: {frozen.human_summary}")
        console.print(tree)
    except Exception as e:
        console.print(f"[bold red]Error freezing ASO:[/bold red] {str(e)}")
        raise SystemExit(1)


if __name__ == "__main__":
    app()
