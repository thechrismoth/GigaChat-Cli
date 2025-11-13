from textual.widgets import Static

from gigachat_cli.widgets.selector import SelectorWidget


class SelectorManager:
    """Менеджер для управления селекторами (выпадающими списками)"""
    
    def __init__(self, screen):
        """
        Инициализация менеджера селекторов
        
        Args:
            screen: Экран для управления отображением
        """
        self.screen = screen
        self.selector_active = False
        self.selector_index = 0
        self.selector_items = []
        self.selector_title = ""
        self.selector_callback = None
        self.selector_widget = None
        self.selector_instruction = None
    
    def show_selector(self, items: list, title: str = "Выберите опцию:", callback=None) -> None:
        """
        Отображение селектора на экране
        
        Args:
            items: Список элементов для выбора
            title: Заголовок селектора
            callback: Функция обратного вызова при выборе элемента
        """
        self.selector_active = True
        self.selector_index = 0
        self.selector_items = items
        self.selector_title = title
        self.selector_callback = callback
        
        # Очистка чата перед показом селектора
        self.screen.clear_chat_display()
        
        # Блокировка поля ввода
        message_input = self.screen.query_one("#message_input")
        message_input.disabled = True
        message_input.placeholder = ""
        message_input.blur()
        
        # Создание виджета селектора
        self.selector_widget = SelectorWidget()
        self.selector_widget.items = items
        self.selector_widget.selected_index = 0
        
        # Добавление заголовка в Markdown
        selector_content = f"**{title}**\n\n"
        self.screen.update_chat_display(selector_content)
        
        # Монтирование виджета селектора в контейнер чата
        chat_container = self.screen.query_one("#chat_container")
        chat_container.mount(self.selector_widget)
        
        # Добавление инструкции по использованию
        instruction = Static("\n  Используйте ↑↓ для выбора, Enter для подтверждения, Esc для отмены")
        chat_container.mount(instruction)
        self.selector_instruction = instruction

    def _update_selector_display(self) -> None:
        """Обновление отображения селектора"""
        if self.selector_widget:
            self.selector_widget.selected_index = self.selector_index
            self.selector_widget.refresh()
    
    def select_next_item(self) -> None:
        """Выбор следующего элемента в селекторе"""
        if self.selector_active:
            self.selector_index = (self.selector_index + 1) % len(self.selector_items)
            self._update_selector_display()

    def select_previous_item(self) -> None:
        """Выбор предыдущего элемента в селекторе"""
        if self.selector_active:
            self.selector_index = (self.selector_index - 1) % len(self.selector_items)
            self._update_selector_display()

    def confirm_selection(self) -> None:
        """Подтверждение выбора текущего элемента"""
        if self.selector_active:
            selected_item = self.selector_items[self.selector_index]
            
            # Удаление виджетов селектора перед вызовом callback
            if self.selector_widget:
                self.selector_widget.remove()
            if self.selector_instruction:
                self.selector_instruction.remove()
            
            # Разблокировка поля ввода
            message_input = self.screen.query_one("#message_input")
            message_input.disabled = False
            message_input.placeholder = "Введите сообщение... (Нажмите Enter для отправки)"
            message_input.focus()
            
            # Вызов callback функции если она задана
            if self.selector_callback:
                self.selector_callback(selected_item, self.selector_index)
            
            # Сброс состояния селектора
            self.selector_active = False
            
            # Возврат фокуса на поле ввода
            self.screen.query_one("#message_input").focus()
    
    def cancel_selection(self) -> None:
        """Отмена выбора и закрытие селектора"""
        if self.selector_active:
            # Удаление виджетов селектора при отмене
            if self.selector_widget:
                self.selector_widget.remove()
            if self.selector_instruction:
                self.selector_instruction.remove()

            # Разблокировка поля ввода
            message_input = self.screen.query_one("#message_input")
            message_input.disabled = False
            message_input.placeholder = "Введите сообщение... (Нажмите Enter для отправки)"
            message_input.focus()
            
            # Сброс состояния селектора
            self.selector_active = False
            
            # Отображение сообщения об отмене
            self.screen.update_chat_display("❌ Выбор отменен")
            
            # Возврат фокуса на поле ввода
            self.screen.query_one("#message_input").focus()
