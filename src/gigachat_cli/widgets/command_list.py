from textual.widgets import Static

class CommandList(Static):
    
    # Обновляем список
    def update_commands(self, commands: list[str], command_handler=None) -> None:
        if commands:
            formatted_commands = []
            for cmd in commands:
                if cmd.startswith('model '):
                    # Для моделей показываем красивое имя
                    model_key = cmd[6:]  # Убираем "model "
                    display_name = command_handler.get_model_display_name(model_key) if command_handler else model_key
                    formatted_commands.append(f"• {display_name}")
                else:
                    formatted_commands.append(f"• {cmd}")
            
            self.update("\n".join(formatted_commands))
            self.remove_class("hidden")
        else:
            self.add_class("hidden")

