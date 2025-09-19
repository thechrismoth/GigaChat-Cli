import os
import typer

from gigachat import GigaChat

giga = GigaChat(
    credentials=os.getenv("GIGACHAT_API_KEY"),
    verify_ssl_certs=False
)

#получаем ответ от нейросети
def get_answer(prompt):
    response = giga.chat(prompt)
    answer = response.choices[0].message.content
    return answer
   

