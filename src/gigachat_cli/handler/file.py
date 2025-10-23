import re
import asyncio

from textual.widgets import TextArea

from gigachat_cli.utils.openfile import open_file
from gigachat_cli.widgets.typing import TypingIndicator

# Хендлер обработки команды /file
class FileHandler:
    async def handle(self, user_text: str, text_area: TextArea, screen):
        if not user_text.lower().startswith('/file'):
            return False
        
        match = re.match(r'/file\s+(\S+)\s+(.+)', user_text)
        
        if match:
            filename = match.group(1)
            message = match.group(2).strip()

            file = open_file(filename)

            if file.startswith("Ошибка"):
                screen.user_inputs.append(("Система", file))
                screen.update_chat_display()
                return True 
            
            screen.user_inputs.append(("Вы", f"{message}\n```\n{file}\n```"))    
            screen.update_chat_display()

            screen.current_typing_indicator = TypingIndicator()
            chat_container = screen.query_one("#chat_container")
            chat_container.mount(screen.current_typing_indicator)

            asyncio.create_task(screen.get_bot_response(f"{message}\n```\n{file}\n```"))

            return True
        
        return False
             
