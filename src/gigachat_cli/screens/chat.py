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
from gigachat_cli.utils.command import CommandHandler
from gigachat_cli.widgets.banner import Banner
from gigachat_cli.widgets.dir import Dir
from gigachat_cli.widgets.typing import TypingIndicator

class ChatScreen(Screen):
    CSS = importlib.resources.files("gigachat_cli.styles").joinpath("chat.css").read_text()
    
    def __init__(self):
        super().__init__()
        self.command_handler = CommandHandler()  # Создаем экземпляр обработчика

    def compose(self) -> ComposeResult:
        yield Banner(classes="banner")
        with VerticalScroll(id="chat_container"):
            yield Markdown("", id="chat_display")
        yield TextArea(
            placeholder="Введите сообщение... (Используйте Shift+Enter для отправки)", 
            id="message_input"
        )
        yield Dir(classes="dir")

    def on_mount(self) -> None:
        self.user_inputs = [] 
        self.current_typing_indicator = None
        self.query_one("#message_input").focus()
        self._update_directory_display()  # Обновляем отображение директории при запуске
    
    # Обработчик буфера обмена
    def on_paste(self, event: events.Paste) -> None:
        text_area = self.query_one("#message_input", TextArea)
        
        if event.text:
            text_area.insert(event.text)
        
        event.prevent_default()
    
    def on_key(self, event: events.Key) -> None:
        if event.key == "shift+enter":
            asyncio.create_task(self.process_message())
            event.prevent_default() 
    
    # Оработка полученного сообщения
    async def process_message(self) -> None:
        text_area = self.query_one("#message_input", TextArea)
        user_text = text_area.text.strip()

        if not user_text:
            return
        
        # Выход из приложения
        if user_text.lower().startswith('/exit'):
            self.app.exit("Результат работы")
            return
        
        # Вызов обработчика терминальных команд
        is_terminal, terminal_command = CommandHandler.is_terminal_command(user_text)
        if is_terminal:
            await self.handle_terminal_command(terminal_command, text_area)
            return
        
        # Вызов обработчика работы с файлами
        if user_text.lower().startswith('/file'):
            await self.handle_file_command(user_text, text_area)
            return
        
        # Вызов обработки обращения к API GigaChat
        await self.handle_gigachat_message(user_text, text_area)
    
    # Обработка терминальных команд
    async def handle_terminal_command(self, command: str, text_area: TextArea) -> None:
        self.user_inputs.append(("Вы", f"`!{command}`"))
        self.update_chat_display()
        
        self.current_typing_indicator = TypingIndicator()
        chat_container = self.query_one("#chat_container")
        chat_container.mount(self.current_typing_indicator)
        
       
        success, output, return_code = await self.command_handler.execute_system_command(command)
        
        if self.current_typing_indicator:
            self.current_typing_indicator.stop_animation()
            self.current_typing_indicator.remove()
            self.current_typing_indicator = None
        
        formatted_output = CommandHandler.format_command_output(output, success, return_code)
        self.user_inputs.append(("Система", formatted_output))
        
        # Обновляем отображение директории после выполнения команды
        self._update_directory_display()
        
        self.update_chat_display()
        text_area.text = ""
        text_area.focus()
    
    # Обработка комады /file для работы с файлами
    async def handle_file_command(self, user_text: str, text_area: TextArea) -> None:
        match = re.match(r'/file\s+(\S+)\s+(.+)', user_text)

        if match:
            filename = match.group(1)
            message = match.group(2).strip()
            
            # Используем текущую директорию из обработчика команд
            current_dir = self.command_handler.get_current_directory()
            file = open_file(filename, base_dir=current_dir)

            if file.startswith("Ошибка"):
                self.user_inputs.append(("Система", file))
                self.update_chat_display()
                return
            
            self.user_inputs.append(("Вы", f"{message}\n```\n{file}\n```"))    
            self.update_chat_display()

            self.current_typing_indicator = TypingIndicator()
            chat_container = self.query_one("#chat_container")
            chat_container.mount(self.current_typing_indicator)

            asyncio.create_task(self.get_bot_response(f"{message}\n```\n{file}\n```"))
    
    # Обработка сообщений к API
    async def handle_gigachat_message(self, user_text: str, text_area: TextArea) -> None:
        self.user_inputs.append(("Вы", user_text))
        self.update_chat_display()

        self.current_typing_indicator = TypingIndicator()
        chat_container = self.query_one("#chat_container")
        chat_container.mount(self.current_typing_indicator)

        asyncio.create_task(self.get_bot_response(user_text))
        
        text_area.text = ""
        text_area.focus()
    
    # Обновляем виджет текущей дирректории
    def _update_directory_display(self) -> None:
        dir_widget = self.query_one(Dir)
        current_dir = self.command_handler.get_current_directory()
        dir_widget.current_dir = str(current_dir)
        dir_widget.refresh()    
        
    # Обновляем отображение чата
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

        self.query_one("#chat_container").scroll_end()
    
    # Получаем ответ и выводим на экран
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
