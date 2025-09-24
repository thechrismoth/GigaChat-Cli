import os

#получаем ответ от нейросети
def get_answer(prompt):
    from langchain_core.messages import HumanMessage
    from langchain_gigachat.chat_models import GigaChat
    
    giga = GigaChat(
        credentials = os.getenv("GIGACHAT_API_KEY"),
        verify_ssl_certs =False
    )

    messages = []

    messages.append(HumanMessage(content=prompt))
    res = giga.invoke(messages)
    messages.append(res)
    return res.content
   

