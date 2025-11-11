from textual.widgets import Input

from gigachat_cli.utils.command import CommandUtils
from gigachat_cli.widgets.typing import TypingIndicator

class TerminalHandler:
    def __init__(self, command_utils: CommandUtils):
        super().__init__()
        self.command_utils = command_utils  

    async def handle(self, user_text: str, input_field: Input, screen):
        is_terminal, command = CommandUtils.is_terminal_command(user_text) 
        if is_terminal:
            # Показываем команду
            screen.update_chat_display(f"**Вы:** `!{command}`")

            screen.current_typing_indicator = TypingIndicator()
            chat_container = screen.query_one("#chat_container")
            chat_container.mount(screen.current_typing_indicator)
        
            success, output, return_code = await self.command_utils.execute_system_command(command)
        
            if screen.current_typing_indicator:
                screen.current_typing_indicator.stop_animation()
                screen.current_typing_indicator.remove()
                screen.current_typing_indicator = None
        
            formatted_output = CommandUtils.format_command_output(output, success, return_code)
            
            # Показываем результат команды
            screen.update_chat_display(f"**Вы:** `!{command}`\n\n**Система:**\n\n{formatted_output}")
        
            # Обновляем отображение директории после выполнения команды
            screen._update_directory_display()
        
            input_field.value = ""
            input_field.focus()
            return True
        return False
