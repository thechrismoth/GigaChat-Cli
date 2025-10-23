from textual.widgets import TextArea

from gigachat_cli.utils.command import CommandUtils
from gigachat_cli.widgets.typing import TypingIndicator

class TerminalHandler:
    def __init__(self, command_utils: CommandUtils):
        super().__init__()
        self.command_utils = command_utils  

    async def handle(self, user_text: str, text_area: TextArea, screen):
        is_terminal, command = CommandUtils.is_terminal_command(user_text) 
        if is_terminal:

            screen.user_inputs.append(("Вы", f"`!{command}`"))
            screen.update_chat_display()
        
            screen.current_typing_indicator = TypingIndicator()
            chat_container = screen.query_one("#chat_container")
            chat_container.mount(screen.current_typing_indicator)
        
       
            success, output, return_code = await self.command_utils.execute_system_command(command)
        
            if screen.current_typing_indicator:
                screen.current_typing_indicator.stop_animation()
                screen.current_typing_indicator.remove()
                screen.current_typing_indicator = None
        
            formatted_output = CommandUtils.format_command_output(output, success, return_code)
            screen.user_inputs.append(("Система", formatted_output))
        
            # Обновляем отображение директории после выполнения команды
            screen._update_directory_display()
        
            screen.update_chat_display()
            text_area.text = ""
            text_area.focus()
            return True
        return False
