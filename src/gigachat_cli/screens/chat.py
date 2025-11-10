import importlib.resources
import asyncio

from textual.app import ComposeResult
from textual.widgets import Input, Markdown, Static
from textual.screen import Screen
from textual.containers import VerticalScroll, Horizontal
from textual import events

from gigachat_cli.utils.config import Config
from gigachat_cli.utils.core import get_answer
from gigachat_cli.utils.command import CommandUtils
from gigachat_cli.utils.list import ListUtils

from gigachat_cli.handler.file import FileHandler
from gigachat_cli.handler.model import ModelHandler
from gigachat_cli.handler.terminal_command import TerminalHandler

from gigachat_cli.widgets.command_list import CommandList
from gigachat_cli.widgets.model import Model
from gigachat_cli.widgets.banner import Banner
from gigachat_cli.widgets.dir import Dir
from gigachat_cli.widgets.typing import TypingIndicator
from gigachat_cli.widgets.selector import SelectorWidget

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
            ModelHandler(self.cfg, self),  # Передаем screen в ModelHandler
            TerminalHandler(self.command_utils)
        ]        

    def compose(self) -> ComposeResult:
        yield Banner(classes="banner")
        with VerticalScroll(id="chat_container"):
            yield Markdown("", id="chat_display")
        yield CommandList(id="command_list", classes="hidden") 
        yield Input(
            placeholder="Введите сообщение... (Нажмите Enter для отправки)", 
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

    def on_input_changed(self, event: Input.Changed) -> None:
        input_field = event.input
        command_list = self.query_one("#command_list", CommandList)

        if self.list_utils.should_show_commands(input_field.value):
            filtered_commands = self.list_utils.get_filtered_commands(input_field.value)
            command_list.update_commands(filtered_commands)

        else:
            command_list.add_class("hidden")
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        command_list = self.query_one("#command_list", CommandList)
        
        # Если активен селектор, не обрабатываем обычный Enter
        if hasattr(self, 'selector_active') and self.selector_active:
            event.prevent_default()
            return
            
        asyncio.create_task(self.process_message())
        command_list.add_class("hidden")
        event.prevent_default()
    
    def on_key(self, event: events.Key) -> None:
        """Обрабатывает нажатия клавиш для селектора"""
        if hasattr(self, 'selector_active') and self.selector_active:
            if event.key == "down":
                self.select_next_item()
                event.prevent_default()
            elif event.key == "up":
                self.select_previous_item()
                event.prevent_default()
            elif event.key == "enter":
                self.confirm_selection()
                event.prevent_default()
            elif event.key == "escape":
                self.cancel_selection()
                event.prevent_default()
    
    # Оработка полученного сообщения
    async def process_message(self) -> None:
        input_field = self.query_one("#message_input", Input)
        user_text = input_field.value.strip()

        if not user_text:
            return
        
        # Выход из приложения
        if user_text.lower().startswith('/exit'):
            self.app.exit("Результат работы")
            return
        
        for handle in self.handlers:
            if await handle.handle(user_text, input_field, self):
                return
        
        # Вызов обработки обращения к API GigaChat
        await self.handle_gigachat_message(user_text, input_field)
    
    # Обработка сообщений к API
    async def handle_gigachat_message(self, user_text: str, input_field: Input) -> None:
        self.user_inputs.append(("Вы", user_text))
        self.update_chat_display()

        self.current_typing_indicator = TypingIndicator()
        chat_container = self.query_one("#chat_container")
        chat_container.mount(self.current_typing_indicator)

        asyncio.create_task(self.get_bot_response(user_text))
        
        input_field.value = ""
        input_field.focus()

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

    # Универсальные методы для интерактивного выбора
    def show_selector(self, items: list, title: str = "Выберите опцию:", callback=None) -> None:
        """Универсальный метод для показа интерактивного списка"""
        self.selector_active = True
        self.selector_index = 0
        self.selector_items = items
        self.selector_title = title
        self.selector_callback = callback
        
        # Создаем виджет селектора
        self.selector_widget = SelectorWidget()
        self.selector_widget.items = items
        self.selector_widget.selected_index = 0
        
        # Добавляем в чат
        selector_content = f"**{title}**\n\n"
        self.user_inputs.append(("Система", selector_content))
        self.update_chat_display()
        
        # Монтируем виджет после обновления чата
        chat_container = self.query_one("#chat_container")
        chat_container.mount(self.selector_widget)
        
        # Добавляем инструкцию
        instruction = Static("Используйте ↑↓ для выбора, Enter для подтверждения, Esc для отмены")
        chat_container.mount(instruction)
        self.selector_instruction = instruction

    def _update_selector_display(self) -> None:
        """Обновляет отображение селектора"""
        if hasattr(self, 'selector_widget') and self.selector_widget:
            self.selector_widget.selected_index = self.selector_index
            self.selector_widget.refresh()

    def select_next_item(self) -> None:
        """Выбирает следующий элемент в списке"""
        if hasattr(self, 'selector_active') and self.selector_active:
            self.selector_index = (self.selector_index + 1) % len(self.selector_items)
            self._update_selector_display()

    def select_previous_item(self) -> None:
        """Выбирает предыдущий элемент в списке"""
        if hasattr(self, 'selector_active') and self.selector_active:
            self.selector_index = (self.selector_index - 1) % len(self.selector_items)
            self._update_selector_display()

    def confirm_selection(self) -> None:
        """Подтверждает выбор"""
        if hasattr(self, 'selector_active') and self.selector_active:
            selected_item = self.selector_items[self.selector_index]
            
            # Удаляем виджеты
            if hasattr(self, 'selector_widget') and self.selector_widget:
                self.selector_widget.remove()
            if hasattr(self, 'selector_instruction') and self.selector_instruction:
                self.selector_instruction.remove()
            
            # Вызываем callback если он есть
            if self.selector_callback:
                self.selector_callback(selected_item, self.selector_index)
            
            # Сбрасываем селектор
            self.selector_active = False

    def cancel_selection(self) -> None:
        """Отменяет выбор"""
        if hasattr(self, 'selector_active') and self.selector_active:
            # Удаляем виджеты
            if hasattr(self, 'selector_widget') and self.selector_widget:
                self.selector_widget.remove()
            if hasattr(self, 'selector_instruction') and self.selector_instruction:
                self.selector_instruction.remove()
            
            self.user_inputs.append(("Система", "❌ Выбор отменен"))
            self.selector_active = False
            self.update_chat_display()
