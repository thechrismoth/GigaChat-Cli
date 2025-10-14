import importlib.resources
import asyncio
import re

from textual.app import ComposeResult
from textual.widgets import TextArea, Markdown
from textual.screen import Screen
from textual.containers import VerticalScroll
from textual import events

from gigachat_cli.utils.core import get_answer
from gigachat_cli.utils.openfile import open_file
from gigachat_cli.widgets.banner import Banner
from gigachat_cli.widgets.dir import Dir
from gigachat_cli.widgets.typing import TypingIndicator

class ChatScreen(Screen):
    CSS = importlib.resources.read_text("gigachat_cli.styles", "chat.css")

    def compose(self) -> ComposeResult:
        yield Banner(classes="banner")
        with VerticalScroll(id="chat_container"):
            yield Markdown("", id="chat_display")
        yield TextArea(
            placeholder="Введите сообщение... (Используйте Shift+Enter для отправки)", 
            id="message_input"
        )
        yield Dir(classes="dir")

    def on_paste(self, event: events.Paste) -> None:
        """Обработчик вставки из буфера обмена"""
        text_area = self.query_one("#message_input", TextArea)
        
        # Вставляем текст в текущую позицию курсора
        if event.text:
            text_area.insert(event.text)
        
        event.prevent_default()
    
    def on_mount(self) -> None:
        self.user_inputs = [] 
        self.current_typing_indicator = None
        self.query_one("#message_input").focus() 
    
    #обработка комбинации для отправки сообщения 
    def on_key(self, event: events.Key) -> None:
         if event.key == "shift+enter":
            asyncio.create_task(self.process_message())
            event.prevent_default() 
 
    #обработка отправки сообщения
    async def process_message(self) -> None:
        text_area = self.query_one("#message_input", TextArea)
        user_text = text_area.text.strip()

        if not user_text:
            return

        if user_text.lower().startswith('/exit'):
            self.app.exit("Результат работы")
            return

        if user_text.lower().startswith('/file'):
            match = re.match(r'/file\s+(\S+)\s+(.+)', user_text)

            if match:
                filename = match.group(1)
                message = match.group(2).strip()
                
                file = open_file(filename)

                if file.startswith("Ошибка"):
                    self.user_inputs.append(("Система", file))
                    self.update_chat_display()
                    return
                
                self.user_inputs.append(("Вы", f"{message}\n```\n{file}\n```"))    
                # Обновляем отображение с Markdown
                self.update_chat_display()

                # Показываем индикатор набора
                self.current_typing_indicator = TypingIndicator()
                chat_container = self.query_one("#chat_container")
                chat_container.mount(self.current_typing_indicator)

                # Запускаем получение ответа от бота в фоне
                asyncio.create_task(self.get_bot_response(f"{message}\n```\n{file}\n```"))

        else:
            # Добавляем сообщение пользователя
            self.user_inputs.append(("Вы", user_text))

            # Обновляем отображение с Markdown
            self.update_chat_display()

            # Показываем индикатор набора
            self.current_typing_indicator = TypingIndicator()
            chat_container = self.query_one("#chat_container")
            chat_container.mount(self.current_typing_indicator)

            # Запускаем получение ответа от бота в фоне
            asyncio.create_task(self.get_bot_response(user_text))

        # Очищаем поле ввода
        text_area.text = ""
        text_area.focus()
    
    #функция обновления отображения чата
    def update_chat_display(self) -> None:
        output_lines = []
        for sender, text in self.user_inputs:
            if sender == "Вы":
                output_lines.append(f"**{sender}:** {text}")
            else:
                output_lines.append(f"**{sender}:**\n\n{text}")
        
        output = "\n\n".join(output_lines)
        
        chat_display = self.query_one("#chat_display", Markdown)
        chat_display.update(output)
    
    #вызываем функцию получения ответа от API и выводим на экран
    async def get_bot_response(self, user_text: str) -> None:
        try:
            bot_response = await get_answer(user_text)
            
            if self.current_typing_indicator:
                self.current_typing_indicator.stop_animation()
                self.current_typing_indicator.remove()
                self.current_typing_indicator = None
            
            self.user_inputs.append(("GigaChat", bot_response))
            
            if len(self.user_inputs) > 10:
                self.user_inputs = self.user_inputs[-10:]
            
            self.update_chat_display()
            
        except Exception as e:
            if self.current_typing_indicator:
                self.current_typing_indicator.stop_animation()
                self.current_typing_indicator.remove()
                self.current_typing_indicator = None
            self.user_inputs.append(("GigaChat", f"**Ошибка:** {str(e)}"))
            self.update_chat_display()
    
    def on_unmount(self) -> None:
        if self.current_typing_indicator:
            self.current_typing_indicator.stop_animation()
