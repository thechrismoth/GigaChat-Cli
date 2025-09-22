import typer
import os

from rich.progress import Progress, SpinnerColumn, TextColumn

from .core import get_answer, draw_menu

app = typer.Typer()

@app.command()
def chat():
    draw_menu()

    while True:
        user_input = typer.prompt("Вы")
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            typer.echo("До свидания!")
            break
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(description="Processing...", total=None)
                result = get_answer(user_input) 

            response = f"GigaChat: {result}"
            typer.echo(response) 
        except Exception as e:
            typer.secho(f"Чат завершил ! свою работу с ошибкой {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)

    dir = os.path.abspath(os.curdir)
    typer.echo(dir)
