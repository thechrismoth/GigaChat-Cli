import re
import asyncio

from textual.widgets import Input

from gigachat_cli.utils.openfile import open_file
from gigachat_cli.widgets.typing import TypingIndicator

# Хендлер обработки команды /file
class FileHandler:
    async def handle(self, user_text: str, input_field: Input, screen):
        if not user_text.lower().startswith('/file'):
            return False
        
        match = re.match(r'/file\s+(\S+)\s+(.+)', user_text)
        
        if match:
            filename = match.group(1)
            message = match.group(2).strip()

            file = open_file(filename)

            if file.startswith("Ошибка"):
                # Показываем ошибку
                screen.update_chat_display(f"**Вы:** {user_text}\n\n**Система:** {file}")
                return True 
            
            # Показываем вопрос с файлом
            screen.update_chat_display(f"**Вы:** {message}\n```\n{file}\n```")

            screen.current_typing_indicator = TypingIndicator()
            chat_container = screen.query_one("#chat_container")
            chat_container.mount(screen.current_typing_indicator)

            # Отправляем в нейросеть
            asyncio.create_task(screen.get_bot_response(f"{message}\n```\n{file}\n```"))

            return True
        
        return False
