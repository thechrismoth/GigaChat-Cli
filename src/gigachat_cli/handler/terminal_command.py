from textual.widgets import Input

from gigachat_cli.utils.command import CommandUtils
from gigachat_cli.widgets.typing import TypingIndicator


class TerminalHandler:
    """Обработчик терминальных команд (начинающихся с !)"""
    
    def __init__(self, command_utils: CommandUtils):
        """
        Инициализация обработчика терминальных команд
        
        Args:
            command_utils: Утилита для выполнения системных команд
        """
        super().__init__()
        self.command_utils = command_utils  

    async def handle(self, user_text: str, input_field: Input, screen) -> bool:
        """
        Обработка терминальной команды
        
        Args:
            user_text: Текст сообщения пользователя
            input_field: Поле ввода для управления
            screen: Экран чата для обновления отображения
            
        Returns:
            bool: True если команда обработана, False если нет
        """
        # Проверка является ли сообщение терминальной командой
        is_terminal, command = CommandUtils.is_terminal_command(user_text) 
        if is_terminal:
            # Отображение выполненной команды пользователя
            screen.update_chat_display(f"**Вы:** `!{command}`")

            # Показ индикатора выполнения команды
            screen.current_typing_indicator = TypingIndicator()
            chat_container = screen.query_one("#chat_container")
            chat_container.mount(screen.current_typing_indicator)
        
            # Выполнение системной команды
            success, output, return_code = await self.command_utils.execute_system_command(command)
        
            # Остановка и удаление индикатора выполнения
            if screen.current_typing_indicator:
                screen.current_typing_indicator.stop_animation()
                screen.current_typing_indicator.remove()
                screen.current_typing_indicator = None
        
            # Форматирование вывода команды
            formatted_output = CommandUtils.format_command_output(output, success, return_code)
            
            # Отображение результата выполнения команды
            screen.update_chat_display(f"**Вы:** `!{command}`\n\n**Система:**\n\n{formatted_output}")
        
            # Обновление отображения текущей директории после выполнения команды
            screen._update_directory_display()
        
            # Очистка поля ввода и возврат фокуса
            input_field.value = ""
            input_field.focus()
            return True
            
        return False
