import typer
from app.commands.start_app import start

app = typer.Typer(help="🚀 Personal DevOps Assistant")

@app.command("start")
def start_command():
    start()