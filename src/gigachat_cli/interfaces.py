import os

from rich.console import Console

console = Console()

#Функция отрисовки интерфейса
def draw_interface(messages):
    console.clear()

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
    console.print(f"[bold green]{ASCII_ART}[/bold green]")
    console.print(f"Советы перед началом работы:\n1.Задавайте вопросы или выполняйте команды.\n2.Будьте конкретны для лучшего результата\n\n")

    for message in messages:
        console.print(message)

    if not messages:
        console.print("[dim]--- История чата пуста ---[/dim]")
        console.print()
    
    current_dir = os.path.abspath(os.curdir)
    console.print(f"\n💬[bold yellow]Поле ввода | 📁 Директория:[/bold yellow]{current_dir}")
    


    

