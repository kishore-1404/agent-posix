import click
from rich.console import Console
from rich.tree import Tree

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


if __name__ == "__main__":
    app()
