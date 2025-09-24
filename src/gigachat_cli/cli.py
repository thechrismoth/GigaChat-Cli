import typer

from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console
from rich.prompt import Prompt

from .core import get_answer
from .interfaces import draw_interface, draw_start_menu

console = Console()
app = typer.Typer()

@app.command()
def main():
    choice = draw_start_menu()
    
    if choice == 'start':
        chat() 

def chat():
    chat_history = []
    
    while True:
        draw_interface(chat_history)
        user_input = Prompt.ask("Ввод ")
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            typer.echo("До свидания!")
            break
        
        chat_history.append(f"[bold blue]Вы:[/bold blue]{user_input}")

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(description="Ожидаем ответ...", total=None)
                result = get_answer(user_input) 
            
            chat_history.append(f"[bold green]GigaChat:[/bold green]{result}")
            if len(chat_history) > 10:
                chat_history = chat_history[-10:]
              
        except Exception as e:
            typer.secho(f"Чат завершил ! свою работу с ошибкой {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
    
