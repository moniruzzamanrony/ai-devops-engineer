import typer
from app.commands.start import start
from app.commands.deploy import deploy
from app.commands.version import version
from app.commands.config import config

app = typer.Typer(help="[*] Rony CLI - DevOps Assistant")

# Register commands directly
app.command()(start)
app.command()(deploy)
app.command()(config)
app.command()(version)