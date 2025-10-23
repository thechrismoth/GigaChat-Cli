import importlib.resources
import asyncio

from textual.app import ComposeResult
from textual.widgets import TextArea, Markdown
from textual.screen import Screen
from textual.containers import VerticalScroll, Horizontal
from textual import events

from gigachat_cli.utils.config import Config
from gigachat_cli.utils.core import get_answer
from gigachat_cli.utils.command import CommandUtils
from gigachat_cli.utils.list import ListUtils
from gigachat_cli.utils.config import Config

from gigachat_cli.handler.file import FileHandler
from gigachat_cli.handler.model import ModelHandler
from gigachat_cli.handler.terminal_command import TerminalHandler

from gigachat_cli.widgets.command_list import CommandList
from gigachat_cli.widgets.model import Model
from gigachat_cli.widgets.banner import Banner
from gigachat_cli.widgets.dir import Dir
from gigachat_cli.widgets.typing import TypingIndicator

class ChatScreen(Screen):
    CSS = importlib.resources.files("gigachat_cli.styles").joinpath("chat.css").read_text()
    
    def __init__(self):
        super().__init__()
        # Обработчики утилит
        self.command_utils = CommandUtils()
        self.list_utils = ListUtils()
        self.cfg = Config()
        # Обработчик хендлеров 
        self.handlers =[
            FileHandler(),
            ModelHandler(self.cfg),
            TerminalHandler(self.command_utils)
        ]        

    def compose(self) -> ComposeResult:
        yield Banner(classes="banner")
        with VerticalScroll(id="chat_container"):
            yield Markdown("", id="chat_display")
        yield CommandList(id="command_list", classes="hidden") 
        yield TextArea(
            placeholder="Введите сообщение... (Используйте Shift+Enter для отправки)", 
            id="message_input"
        )
        with Horizontal(classes="status_bar"):
            yield Dir(classes="dir")
            yield Model(classes="model")

    def on_mount(self) -> None:
        self.user_inputs = [] 
        self.current_typing_indicator = None
        self.query_one("#message_input").focus()
        self._update_directory_display()
        self.query_one("#command_list", CommandList).add_class("hidden")

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        text_area = event.text_area
        command_list = self.query_one("#command_list", CommandList)

        if self.list_utils.should_show_commands(text_area.text):
            filtered_commands = self.list_utils.get_filtered_commands(text_area.text)
            command_list.update_commands(filtered_commands)

        else:
            command_list.add_class("hidden")
    
    def on_key(self, event: events.Key) -> None:
        command_list = self.query_one("#command_list", CommandList)

        if event.key == "shift+enter":
            asyncio.create_task(self.process_message())
            command_list.add_class("hidden")
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
        
        for handle in self.handlers:
            if await handle.handle(user_text,text_area, self):
                return
        
        # Вызов обработки обращения к API GigaChat
        await self.handle_gigachat_message(user_text, text_area)
    
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

    def _update_model_display(self) -> None:
        model_widget = self.query_one(Model)
        current_model = self.cfg.get_model()
        model_widget.current_model = str(current_model)
        model_widget.refresh()
    
    # Обновляем виджет текущей дирректории
    def _update_directory_display(self) -> None:
        dir_widget = self.query_one(Dir)
        current_dir = self.command_utils.get_current_directory()
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

