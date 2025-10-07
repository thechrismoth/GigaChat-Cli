import importlib.resources
import asyncio

from textual.app import ComposeResult
from textual.widgets import Input, Static
from textual.screen import Screen
from textual.containers import VerticalScroll

from gigachat_cli.utils.core import get_answer
from gigachat_cli.widgets.banner import Banner
from gigachat_cli.widgets.dir import Dir
from gigachat_cli.widgets.typing import TypingIndicator

class ChatScreen(Screen):
    CSS = importlib.resources.read_text("gigachat_cli.styles", "chat.css")

    def compose(self) -> ComposeResult:
        yield Banner(classes="banner")
        with VerticalScroll(id="chat_container"):
            yield Static("", id="chat_display")
        yield Input(placeholder="Введите сообщение и нажмите Enter", id="message_input")
        yield Dir(classes="dir")
    
    def on_mount(self) -> None:
        self.user_inputs = [] 
        self.current_typing_indicator = None
        self.query_one("#message_input").focus() 

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if not event.value.strip():
            return
        
        user_text = event.value.strip()

        if user_text.lower() in ['quit', 'exit', 'q']:
            self.app.exit("Результат работы")
            return

        # Добавляем сообщение пользователя
        self.user_inputs.append(("Вы", user_text))
        
        # Обновляем отображение
        output_lines = []
        for sender, text in self.user_inputs:
            output_lines.append(f"{sender}: {text}")
        output = "\n".join(output_lines)
        self.query_one("#chat_display", Static).update(output)
        
        # Показываем индикатор набора
        self.current_typing_indicator = TypingIndicator()
        chat_container = self.query_one("#chat_container")
        chat_container.mount(self.current_typing_indicator)
        
        # Запускаем получение ответа от бота в фоне
        asyncio.create_task(self.get_bot_response(user_text))
        
        event.input.value = ""
    
    #получаем ответ от API
    async def get_bot_response(self, user_text: str) -> None:
        try:
            # Получаем ответ от бота
            bot_response = await get_answer(user_text)
            
            # Убираем индикатор набора
            if self.current_typing_indicator:
                self.current_typing_indicator.stop_animation()
                self.current_typing_indicator.remove()
                self.current_typing_indicator = None
            
            # Добавляем ответ бота
            self.user_inputs.append(("GigaChat", bot_response))
            
            # Оставляем только последние 10 сообщений
            if len(self.user_inputs) > 10:
                self.user_inputs = self.user_inputs[-10:]
            
            # Обновляем отображение
            output_lines = []
            for sender, text in self.user_inputs:
                output_lines.append(f"{sender}: {text}")
            output = "\n".join(output_lines)
            self.query_one("#chat_display", Static).update(output)
            
        except Exception as e:
            # В случае ошибки тоже убираем индикатор
            if self.current_typing_indicator:
                self.current_typing_indicator.stop_animation()
                self.current_typing_indicator.remove()
                self.current_typing_indicator = None
            self.user_inputs.append(("GigaChat", f"Ошибка: {str(e)}"))
            
            output_lines = []
            for sender, text in self.user_inputs:
                output_lines.append(f"{sender}: {text}")
            output = "\n".join(output_lines)
            self.query_one("#chat_display", Static).update(output)
    
    #очищаем при завершении
    def on_unmount(self) -> None:
        if self.current_typing_indicator:
            self.current_typing_indicator.stop_animation()
