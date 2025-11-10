from textual.widgets import Static
from gigachat_cli.widgets.selector import SelectorWidget

class SelectorManager:
    """Менеджер для управления интерактивными селекторами"""
    
    def __init__(self, screen):
        self.screen = screen
        self.selector_active = False
        self.selector_index = 0
        self.selector_items = []
        self.selector_title = ""
        self.selector_callback = None
        self.selector_widget = None
        self.selector_instruction = None
    
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
        self.screen.user_inputs.append(("Система", selector_content))
        self.screen.update_chat_display()
        
        # Монтируем виджет после обновления чата
        chat_container = self.screen.query_one("#chat_container")
        chat_container.mount(self.selector_widget)
        
        # Добавляем инструкцию
        instruction = Static("Используйте ↑↓ для выбора, Enter для подтверждения, Esc для отмены")
        chat_container.mount(instruction)
        self.selector_instruction = instruction

    def _update_selector_display(self) -> None:
        """Обновляет отображение селектора"""
        if self.selector_widget:
            self.selector_widget.selected_index = self.selector_index
            self.selector_widget.refresh()

    def select_next_item(self) -> None:
        """Выбирает следующий элемент в списке"""
        if self.selector_active:
            self.selector_index = (self.selector_index + 1) % len(self.selector_items)
            self._update_selector_display()

    def select_previous_item(self) -> None:
        """Выбирает предыдущий элемент в списке"""
        if self.selector_active:
            self.selector_index = (self.selector_index - 1) % len(self.selector_items)
            self._update_selector_display()

    def confirm_selection(self) -> None:
        """Подтверждает выбор"""
        if self.selector_active:
            selected_item = self.selector_items[self.selector_index]
            
            # Удаляем виджеты
            if self.selector_widget:
                self.selector_widget.remove()
            if self.selector_instruction:
                self.selector_instruction.remove()
            
            # Вызываем callback если он есть
            if self.selector_callback:
                self.selector_callback(selected_item, self.selector_index)
            
            # Сбрасываем селектор
            self.selector_active = False

    def cancel_selection(self) -> None:
        """Отменяет выбор"""
        if self.selector_active:
            # Удаляем виджеты
            if self.selector_widget:
                self.selector_widget.remove()
            if self.selector_instruction:
                self.selector_instruction.remove()
            
            self.screen.user_inputs.append(("Система", "❌ Выбор отменен"))
            self.selector_active = False
            self.screen.update_chat_display()
