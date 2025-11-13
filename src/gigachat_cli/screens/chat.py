import importlib.resources
import asyncio
from typing import Optional

from textual.app import ComposeResult
from textual.widgets import Input, Markdown
from textual.screen import Screen
from textual.containers import VerticalScroll, Horizontal
from textual import events

from gigachat_cli.utils.config import Config
from gigachat_cli.utils.core import get_answer_stream, GigaChatError
from gigachat_cli.utils.command import CommandUtils
from gigachat_cli.utils.list import ListUtils
from gigachat_cli.utils.selector import SelectorManager
from gigachat_cli.utils.file import FileUtils

from gigachat_cli.handler.help import HelpHandler 
from gigachat_cli.handler.model import ModelHandler
from gigachat_cli.handler.terminal_command import TerminalHandler

from gigachat_cli.widgets.command_list import CommandList
from gigachat_cli.widgets.file_list import FileList
from gigachat_cli.widgets.model import Model
from gigachat_cli.widgets.banner import Banner
from gigachat_cli.widgets.recommend import Recommend 
from gigachat_cli.widgets.dir import Dir
from gigachat_cli.widgets.typing import TypingIndicator

class ChatScreen(Screen):
    CSS = importlib.resources.files("gigachat_cli.styles").joinpath("chat.css").read_text()
    
    def __init__(self):
        super().__init__()
        # Обработчики утилит
        self.command_utils = CommandUtils()
        self.list_utils = ListUtils()
        self.file_utils = FileUtils(self.command_utils)
        self.cfg = Config()
        
        # Менеджер селекторов
        self.selector_manager = SelectorManager(self)
        
        # Обработчик хендлеров 
        self.handlers =[
            HelpHandler(),
            ModelHandler(self.cfg, self),
            TerminalHandler(self.command_utils)
        ]
        
        # Состояние для потоковой обработки
        self.current_typing_indicator: Optional[TypingIndicator] = None
        self.current_stream_task: Optional[asyncio.Task] = None
        self.current_response_content: str = ""
        self.is_processing_stream: bool = False
        self.last_user_message: str = ""
        self.conversation_context: list = []  # Сохраняем контекст диалога

    def compose(self) -> ComposeResult:
        yield Banner(classes="banner")
        yield Recommend(classes="recommend")
        with VerticalScroll(id="chat_container"):
            yield Markdown("", id="chat_display")
        yield CommandList(id="command_list", classes="hidden") 
        yield FileList(id="file_list", classes="hidden")
        yield Input(
            placeholder="Введите сообщение... (Нажмите Enter для отправки)", 
            id="message_input"
        )
        with Horizontal(classes="status_bar"):
            yield Dir(classes="dir")
            yield Model(classes="model")

    def on_mount(self) -> None:
        self.current_typing_indicator = None
        self.query_one("#message_input").focus()
        self._update_directory_display()
        self._update_model_display()
        self.query_one("#command_list", CommandList).add_class("hidden")
        self.query_one("#file_list", FileList).add_class("hidden")

    def on_unmount(self) -> None:
        """Очистка ресурсов при размонтировании экрана"""
        self._cleanup_stream_processing()

    def _cleanup_stream_processing(self):
        """Очистка потоковой обработки"""
        if self.current_stream_task and not self.current_stream_task.done():
            self.current_stream_task.cancel()
        self.is_processing_stream = False
        self.current_response_content = ""
        self._hide_typing_indicator()

    def _hide_typing_indicator(self):
        """Скрытие индикатора набора"""
        if self.current_typing_indicator:
            self.current_typing_indicator.stop_animation()
            self.current_typing_indicator.remove()
            self.current_typing_indicator = None

    # обработчик случайных нажатий
    def on_click(self, event: events.Click) -> None:
        if not self.selector_manager.selector_active:
            input_field = self.query_one("#message_input")
            if hasattr(event.widget, 'id') and event.widget.id != "message_input":
                input_field.focus() 
    
    # Обработчик проверка фокуса
    def on_focus(self, event: events.Focus) -> None:
        if not self.selector_manager.selector_active:
            if event.widget.id != "message_input":
                self.query_one("#message_input").focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        input_field = event.input
        command_list = self.query_one("#command_list", CommandList)
        file_list = self.query_one("#file_list", FileList)

        # Сначала проверяем команды
        if self.list_utils.should_show_commands(input_field.value):
            filtered_commands = self.list_utils.get_filtered_commands(input_field.value)
            command_list.update_commands(filtered_commands, input_field.value)
            file_list.add_class("hidden")

        # Затем проверяем файлы для терминальных команд
        elif self.file_utils.should_show_files(input_field.value):
            files, current_command, current_path = self.file_utils.get_files_for_completion(input_field.value)
            if files:
                file_list.update_files(files, current_command, current_path)
                command_list.add_class("hidden")
            else:
                file_list.add_class("hidden")

        else:
            command_list.add_class("hidden")
            file_list.add_class("hidden")
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        command_list = self.query_one("#command_list", CommandList)
        file_list = self.query_one("#file_list", FileList)
        
        # Если активен селектор, не обрабатываем обычный Enter
        if self.selector_manager.selector_active:
            event.prevent_default()
            return

        elif not command_list.has_class("hidden"):
            command_list.apply_selection(event.input)
            event.prevent_default()
            return
        
        elif not file_list.has_class("hidden"):
            file_list.apply_selection(event.input)
            event.prevent_default()
            return
            
        # Если идет потоковая обработка, не обрабатываем новое сообщение
        if self.is_processing_stream:
            event.prevent_default()
            return
            
        asyncio.create_task(self.process_message())
        command_list.add_class("hidden")
        file_list.add_class("hidden")
        event.prevent_default()
        
        # Возвращаем фокус после отправки сообщения
        self.query_one("#message_input").focus()
    
    # Обработчик нажатия клавишь
    def on_key(self, event: events.Key) -> None:
        command_list = self.query_one("#command_list", CommandList)
        file_list = self.query_one("#file_list", FileList)

        if self.selector_manager.selector_active:
            if event.key == "down":
                self.selector_manager.select_next_item()
                event.prevent_default()
            elif event.key == "up":
                self.selector_manager.select_previous_item()
                event.prevent_default()
            elif event.key == "enter":
                self.selector_manager.confirm_selection()
                event.prevent_default()
            elif event.key == "escape":
                self.selector_manager.cancel_selection()
                event.prevent_default() 

        elif not command_list.has_class("hidden"):
            if event.key == "tab":
                command_list.select_next()
                event.prevent_default()
                event.stop()
            elif event.key == "shift+tab":
                command_list.select_previous()
                event.prevent_default()
                event.stop()
            elif event.key == "enter":
                command_list.apply_selection(self.query_one("#message_input"))
                event.prevent_default()
                self.query_one("#message_input").focus()
            elif event.key == "escape":
                command_list.add_class("hidden")
                event.prevent_default()
                self.query_one("#message_input").focus()
        
        # Обработка для file_list
        elif not file_list.has_class("hidden"):
            if event.key == "tab":
                file_list.select_next()
                event.prevent_default()
                event.stop()
            elif event.key == "shift+tab":
                file_list.select_previous()
                event.prevent_default()
                event.stop()
            elif event.key == "enter":
                file_list.apply_selection(self.query_one("#message_input"))
                event.prevent_default()
                self.query_one("#message_input").focus()
            elif event.key == "escape":
                file_list.add_class("hidden")
                event.prevent_default()
                self.query_one("#message_input").focus()
        
        # Обработка TAB когда скрыто автодополнение
        elif event.key == "tab" and command_list.has_class("hidden") and file_list.has_class("hidden"):
            event.prevent_default()
            event.stop()
        
        # Обработка Ctrl+C для отмены потоковой обработки
        elif event.key == "ctrl+c" and self.is_processing_stream:
            self._cleanup_stream_processing()
            self.update_chat_display(f"**Вы:** {self.last_user_message}\n\n**GigaChat:**\n\n*Запрос отменен пользователем*")
            event.prevent_default()
    
    # Оработка полученного сообщения
    async def process_message(self) -> None:
        input_field = self.query_one("#message_input", Input)
        user_text = input_field.value.strip()

        if not user_text:
            return
        
        # Сохраняем сообщение пользователя
        self.last_user_message = user_text
        
        # Выход из приложения
        if user_text.lower().startswith('/exit'):
            self.app.exit("Результат работы")
            return

        if user_text.lower().startswith('/menu'):
            self.app.pop_screen()
            return
         
        # Очищаем визуальный вывод перед новым сообщением
        self.clear_chat_display()
        
        # Сохраняем контекст диалога
        self.conversation_context.append(f"Пользователь: {user_text}")
        if len(self.conversation_context) > 6:  # Ограничиваем контекст
            self.conversation_context = self.conversation_context[-6:]
        
        # Проверяем обработчики команд
        for handler in self.handlers:
            if await handler.handle(user_text, input_field, self):
                return
        
        # Вызов обработки обращения к API GigaChat
        await self.handle_gigachat_message(user_text, input_field)
    
    # Обработка сообщений к API
    async def handle_gigachat_message(self, user_text: str, input_field: Input) -> None:
        # НЕМЕДЛЕННО очищаем поле ввода и показываем сообщение пользователя
        input_field.value = ""
        self.update_chat_display(f"**Вы:** {user_text}")
        
        # НЕМЕДЛЕННО создаем и показываем индикатор набора
        self.current_typing_indicator = TypingIndicator()
        chat_container = self.query_one("#chat_container")
        chat_container.mount(self.current_typing_indicator)
        
        # НЕМЕДЛЕННО запускаем потоковую обработку
        self.is_processing_stream = True
        self.current_stream_task = asyncio.create_task(self.get_bot_response_stream(user_text))
        
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

    # Очистка дисплея
    def clear_chat_display(self) -> None:
        chat_display = self.query_one("#chat_display", Markdown)
        chat_display.update("")
        
        # Очищаем все дополнительные виджеты в контейнере чата
        chat_container = self.query_one("#chat_container")
        for child in chat_container.children:
            if child.id != "chat_display":
                child.remove()
    
    # Обновление отображения чата 
    def update_chat_display(self, content: str = "") -> None:
        chat_display = self.query_one("#chat_display", Markdown)
        chat_display.update(content)
        self.query_one("#chat_container").scroll_end()

    # Обновление отображения чата с потоковым контентом
    def update_chat_display_stream(self, user_text: str, response_content: str) -> None:
        """Обновление отображения с потоковым контентом"""
        full_content = f"**Вы:** {user_text}\n\n**GigaChat:**\n\n{response_content}"
        self.update_chat_display(full_content)

    # Получаем ответ и выводим на экран (потоковая версия)
    async def get_bot_response_stream(self, user_text: str) -> None:
        """Потоковое получение ответа от GigaChat"""
        self.current_response_content = ""
        
        try:
            # НЕМЕДЛЕННО показываем пустой ответ чтобы начать поток
            self.update_chat_display_stream(user_text, "")
            
            first_chunk_received = False
            start_time = asyncio.get_event_loop().time()
            
            # Получаем потоковый ответ
            async for chunk in get_answer_stream(user_text):
                # Если это первый чанк, измеряем время отклика
                if not first_chunk_received:
                    first_chunk_received = True
                    response_time = asyncio.get_event_loop().time() - start_time
                    print(f"First chunk received after: {response_time:.2f} seconds")
                
                if chunk.content:
                    self.current_response_content += chunk.content
                    # Обновляем отображение в реальном времени
                    self.update_chat_display_stream(user_text, self.current_response_content)
                
                if chunk.is_final:
                    break
                    
                # Небольшая задержка для плавного отображения
                await asyncio.sleep(0.01)
            
            # Финальное обновление
            self.update_chat_display_stream(user_text, self.current_response_content)
            
        except GigaChatError as e:
            await self._handle_stream_error(user_text, f"**Ошибка API:** {e.message}")
        except asyncio.CancelledError:
            # Запрос был отменен - ничего не делаем
            pass
        except Exception as e:
            await self._handle_stream_error(user_text, f"**Неизвестная ошибка:** {str(e)}")
        finally:
            self.is_processing_stream = False
            self.current_response_content = ""
            self._hide_typing_indicator()

    async def _handle_stream_error(self, user_text: str, error_message: str):
        """Обработка ошибок потоковой обработки"""
        self.update_chat_display_stream(user_text, error_message)
        self.is_processing_stream = False
        self.current_response_content = ""
        self._hide_typing_indicator()

