import os
import questionary

from rich.console import Console

console = Console()

ASCII_ART = r"""   
       █████████   ███                       █████████  █████                 █████   
      ███░░░░░███ ░░░                       ███░░░░░███░░███                 ░░███    
     ███     ░░░  ████   ███████  ██████   ███     ░░░  ░███████    ██████   ███████  
    ░███         ░░███  ███░░███ ░░░░░███ ░███          ░███░░███  ░░░░░███ ░░░███░   
    ░███    █████ ░███ ░███ ░███  ███████ ░███          ░███ ░███   ███████   ░███    
    ░░███  ░░███  ░███ ░███ ░███ ███░░███ ░░███     ███ ░███ ░███  ███░░███   ░███ ███
     ░░█████████  █████░░███████░░████████ ░░█████████  ████ █████░░████████  ░░█████ 
      ░░░░░░░░░  ░░░░░  ░░░░░███ ░░░░░░░░   ░░░░░░░░░  ░░░░ ░░░░░  ░░░░░░░░    ░░░░░  
                        ███ ░███                                                      
                       ░░██████                                                       
                        ░░░░░░                                                        
    """

#Функция отрисовки стартового меню
def draw_start_menu():
    console.clear()
    
    console.print(f"[bold green]{ASCII_ART}[/bold green]")

    choice = questionary.select(
        "Выберите режим авторизации:",
        choices=[
            questionary.Choice("🚀 Начать использование", "start")
        ],
        qmark=" ",
        pointer="→"
    ).ask()
  
    return choice

#Функция отрисовки интерфейса
def draw_interface(messages):
    console.clear()
 
    console.print(f"[bold green]{ASCII_ART}[/bold green]")
    console.print(f"Советы перед началом работы:\n1.Задавайте вопросы или выполняйте команды.\n2.Будьте конкретны для лучшего результата\n\n")

    for message in messages:
        console.print(message)

    if not messages:
        console.print("[dim]--- История чата пуста ---[/dim]")
        console.print()
    
    current_dir = os.path.abspath(os.curdir)
    console.print(f"\n💬[bold yellow]Поле ввода | 📁 Директория:[/bold yellow]{current_dir}")
    


    

