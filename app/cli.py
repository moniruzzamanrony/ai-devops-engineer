import typer
from app.commands import deploy

app = typer.Typer(help="🚀 Personal DevOps Assistant")

app.add_typer(deploy.app, name="deploy")