import os
import asyncio

#получаем ответ от нейросети
async def get_answer(prompt):
    from langchain_core.messages import HumanMessage
    from langchain_gigachat.chat_models import GigaChat
    
    giga = GigaChat(
        credentials = os.getenv("GIGACHAT_API_KEY"),
        verify_ssl_certs =False
    )

    messages = []
    messages.append(HumanMessage(content=prompt))
    
    # Запускаем синхронный вызов в отдельном потоке
    loop = asyncio.get_event_loop()
    res = await loop.run_in_executor(None, giga.invoke, messages)
    
    messages.append(res)
    return res.content




