from textual.widgets import Static
from textual.reactive import reactive

# Виджет автодополнения команд
class CommandList(Static):
    can_focus = False 
    
    commands = reactive([])
    selected_index = reactive(0)
    current_input = ""  # Сохраняем текущий ввод
    visible_start = 0   # Начало видимой области
    visible_count = 5   # Сколько команд показывать одновременно
    
    def update_commands(self, commands: list[str], current_input: str) -> None:
        if commands:
            self.commands = commands
            self.current_input = current_input
            self.selected_index = 0
            self.visible_start = 0
            self.remove_class("hidden")
            self._update_display()
        else:
            self.add_class("hidden")
            self.commands = []
    
    def _update_display(self) -> None:
        """Обновляет отображение списка команд с описаниями"""
        if not self.commands:
            return
            
        # Получаем команды с описаниями
        commands_with_desc = self.screen.list_utils.get_commands_with_descriptions(self.current_input)
        
        # Определяем видимый диапазон
        visible_commands = commands_with_desc[self.visible_start:self.visible_start + self.visible_count]
        
        formatted_commands = []
        for i, (cmd, description) in enumerate(visible_commands):
            actual_index = self.visible_start + i
            display_cmd = cmd[1:] if cmd.startswith('/') else cmd
            
            # Форматируем строку с выравниванием
            cmd_part = f"{display_cmd:<8}"
            line = f"{cmd_part} - {description}"
            
            # Показываем индикатор прокрутки если есть больше команд
            if actual_index == self.selected_index:
                if len(commands_with_desc) > self.visible_count:
                    line = f"➤ {line} [{actual_index + 1}/{len(commands_with_desc)}]"
                else:
                    line = f"➤ {line}"
            else:
                line = f"  {line}"
            
            formatted_commands.append(line)
        
        self.update("\n".join(formatted_commands))
    
    def select_next(self) -> None:
        if self.commands:
            self.selected_index = (self.selected_index + 1) % len(self.commands)
            # Прокручиваем если вышли за границы видимой области
            if self.selected_index >= self.visible_start + self.visible_count:
                self.visible_start += 1
            elif self.selected_index < self.visible_start:
                self.visible_start = self.selected_index
            self._update_display()
    
    def select_previous(self) -> None:
        if self.commands:
            self.selected_index = (self.selected_index - 1) % len(self.commands)
            # Прокручиваем если вышли за границы видимой области
            if self.selected_index < self.visible_start:
                self.visible_start -= 1
            elif self.selected_index >= self.visible_start + self.visible_count:
                self.visible_start = self.selected_index - self.visible_count + 1
            self._update_display()
    
    def get_selected_command(self) -> str:
        if self.commands and 0 <= self.selected_index < len(self.commands):
            return self.commands[self.selected_index]
        return ""
    
    def apply_selection(self, input_field) -> None:
        selected_cmd = self.get_selected_command()
        if selected_cmd and self.current_input:
            if ' ' in self.current_input:
                last_space_pos = self.current_input.rfind(' ')
                base_text = self.current_input[:last_space_pos + 1]
                new_text = base_text + selected_cmd
            else:
                new_text = selected_cmd
        
            input_field.value = new_text
            input_field.cursor_position = len(new_text)
            self.add_class("hidden")
            input_field.focus()
