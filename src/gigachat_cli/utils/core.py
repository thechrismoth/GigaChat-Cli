import os
import asyncio
from langchain_core.messages import HumanMessage, AIMessage
from langchain_gigachat.chat_models import GigaChat

class GigaChatManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.conversation_history = []
        return cls._instance
    
    async def get_answer(self, prompt: str, clear_history: bool = False) -> str:
        if clear_history:
            self.conversation_history.clear()
            return "История диалога очищена"
        
        giga = GigaChat(
            credentials=os.getenv("GIGACHAT_API_KEY"),
            verify_ssl_certs=False
        )

        messages = self.conversation_history.copy()
        messages.append(HumanMessage(content=prompt))
        
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, giga.invoke, messages)
        
        # Сохраняем в историю
        self.conversation_history.append(HumanMessage(content=prompt))
        self.conversation_history.append(AIMessage(content=res.content))
        
        # Ограничиваем 5 парами сообщений (10 сообщений)
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        
        return res.content
    
    def clear_history(self) -> str:
        self.conversation_history.clear()
        return "История диалога очищена"

# Создаем инстанс
chat_manager = GigaChatManager()

# Функции для обратной совместимости с вашим кодом
async def get_answer(prompt: str, clear_history: bool = False) -> str:
    return await chat_manager.get_answer(prompt, clear_history)

def clear_chat_history() -> str:
    return chat_manager.clear_history()
