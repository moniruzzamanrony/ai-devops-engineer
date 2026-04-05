import typer

app = typer.Typer()

@app.command("start")
def start():
    print("hi")

if __name__ == '__main__':
    app()