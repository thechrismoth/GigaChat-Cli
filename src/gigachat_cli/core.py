import os
import typer

#получаем ответ от нейросети
def get_answer(prompt):
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_gigachat.chat_models import GigaChat

    giga = GigaChat(
        credentials=os.getenv("GIGACHAT_API_KEY"),
        verify_ssl_certs=False
    )

    messages = []


    messages.append(HumanMessage(content=prompt))
    res = giga.invoke(messages)
    messages.append(res)
    return res.content
   
def draw_menu():
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

    typer.secho(ASCII_ART, fg = typer.colors.GREEN)
    typer.echo(f"Советы перед началом работы:\n1.Задавайте вопросы или выполняйте команды.\n2.Будьте конкретны для лучшего результата\n\n")

