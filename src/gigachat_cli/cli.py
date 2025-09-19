import typer

from rich.progress import Progress, SpinnerColumn, TextColumn

from .core import get_answer

app = typer.Typer()

@app.command()
def chat():
    """Простая cli утилита для общение с GigaChat"""
    typer.echo("Добро пожаловать в эхо-чат! Для выхода введите 'quit'")
    typer.echo("                   ░▒██████                               ████████  █████  ████████       █████        ")                  
    typer.echo("              ██████             ░                       ██████████ █████ ██████████     ███████       ")                  
    typer.echo("           ████▒           ▒████████                     ████  ████ █████ ████  ████    ████████       ")                  
    typer.echo("         ████         ▓████████████████                  ████  ████ █████ ████  ████    ████████       ")                  
    typer.echo("       ████        ██████████████████████                ████       █████ ████         ██████████      ")                  
    typer.echo("     ████       ████████████████ █████████               ██████████ █████ ██████████   ██████████      ")                  
    typer.echo("    ████         ░██████████     ██████████              ██████████ █████ ██████████   ██████████      ")                  
    typer.echo("   ████            ██████       ████████████             ████  ████ █████ ████  ████  ████████████     ")                  
    typer.echo("  ░████              █▒       ███████████ ███            ██████████ █████ ██████████  ████    ████     ")                  
    typer.echo("  █████                     ▓████████████  ██░           ██████████ █████ ██████████  ████    ████     ")                  
    typer.echo("  █████                   ██████████████▓   ██             ██████   █████   ██████    ████    █████    ")                  
    typer.echo(" ███████               █████████████████     █                                                         ")                  
    typer.echo(" ████████▓          ███████████████████                                                                ")                  
    typer.echo(" █████████████████████████████████████                                                                 ")                  
    typer.echo(" ██████████████████████████████████░                  ████████  █████  ████     ██████   ████████████  ")                 
    typer.echo("  █████████████████████████████████                   ██████████ █████  ████    ███████   ████████████ ")                  
    typer.echo("   █████████████████████████████▒           ▒         ████  ████ █████  ████    ████████      ████     ")                  
    typer.echo("   ░██████████████████████████             █          ████       █████  ████   █████████      ████     ")                  
    typer.echo("     █████████████████████░              ▒█           ████       ███████████   █████████      ████     ")                  
    typer.echo("        ██████████████                  ██            ████       ███████████   ██████████     ████     ")                  
    typer.echo("                                     ▓███             ████       █████  ████  ███████████     ████     ")                  
    typer.echo("         ▓                        ▓████               ████  ████ █████  ████  ████   ████     ████     ")                  
    typer.echo("           ███                ██████                  ██████████ █████  ████  ████   █████    ████     ")                  
    typer.echo("              ███████████████████                     ██████████ █████  ████ █████    ████    ████     ")                  
    typer.echo("                   ░▒██████                             █████    █████  ████ ████     ████    ████     ")



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
            typer.secho(f"Чат завершил свою работу с ошибкой {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
 
