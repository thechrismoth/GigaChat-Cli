from textual.widgets import Static
from textual.reactive import reactive

# Виджет автодополнения команд
class CommandList(Static):
    
    commands = reactive([])
    selected_index = reactive(0)
    current_input = ""  # Сохраняем текущий ввод
    
    def update_commands(self, commands: list[str], current_input: str) -> None:
        if commands:
            self.commands = commands
            self.current_input = current_input
            self.selected_index = 0
            self.remove_class("hidden")
            self._update_display()
        else:
            self.add_class("hidden")
            self.commands = []
    
    def _update_display(self) -> None:
        """Обновляет отображение списка команд"""
        if not self.commands:
            return
            
        formatted_commands = []
        for i, cmd in enumerate(self.commands):
            # Убираем / для красивого отображения
            display_cmd = cmd[1:] if cmd.startswith('/') else cmd
            if i == self.selected_index:
                formatted_commands.append(f"➤ {display_cmd}")
            else:
                formatted_commands.append(f"  {display_cmd}")
        
        self.update("\n".join(formatted_commands))
    
    # Выбрать следующую команду
    def select_next(self) -> None:
        if self.commands:
            self.selected_index = (self.selected_index + 1) % len(self.commands)
            self._update_display()
    
    # Выбрать предыдущую команду
    def select_previous(self) -> None:
        if self.commands:
            self.selected_index = (self.selected_index - 1) % len(self.commands)
            self._update_display()
    
    # возврат на выбранную команду
    def get_selected_command(self) -> str:
        if self.commands and 0 <= self.selected_index < len(self.commands):
            return self.commands[self.selected_index]
        return ""
    
    # Преминение выбранной команды
    def apply_selection(self, input_field) -> None:
        selected_cmd = self.get_selected_command()
        if selected_cmd and self.current_input:
            # Находим позицию начала последнего слова/части для замены
            if ' ' in self.current_input:
                # Если есть пробелы - заменяем только часть после последнего пробела
                last_space_pos = self.current_input.rfind(' ')
                base_text = self.current_input[:last_space_pos + 1]
                new_text = base_text + selected_cmd
            else:
                # Если пробелов нет - заменяем весь текст
                new_text = selected_cmd
            
            input_field.value = new_text
            # Ставим курсор в конец
            input_field.cursor_position = len(new_text)
            self.add_class("hidden")
