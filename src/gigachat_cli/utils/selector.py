from textual.widgets import Static

from gigachat_cli.widgets.selector import SelectorWidget

# Класс по управлению селекторами
class SelectorManager:
    
    def __init__(self, screen):
        self.screen = screen
        self.selector_active = False
        self.selector_index = 0
        self.selector_items = []
        self.selector_title = ""
        self.selector_callback = None
        self.selector_widget = None
        self.selector_instruction = None
    
    # Вывод списка на экран
    def show_selector(self, items: list, title: str = "Выберите опцию:", callback=None) -> None:
        self.selector_active = True
        self.selector_index = 0
        self.selector_items = items
        self.selector_title = title
        self.selector_callback = callback
        
        # Очищаем чат перед показом селектора
        self.screen.clear_chat_display()
        
        # Убираем фокус с Input и блокируем imput
        message_input = self.screen.query_one("#message_input")
        message_input.disabled = True  # Блокируем ввод
        message_input.placeholder = ""
        message_input.blur()
        
        # Создаем виджет селектора
        self.selector_widget = SelectorWidget()
        self.selector_widget.items = items
        self.selector_widget.selected_index = 0
        
        # Добавляем заголовок в Markdown
        selector_content = f"**{title}**\n\n"
        self.screen.update_chat_display(selector_content)
        
        # Монтируем виджет селектора
        chat_container = self.screen.query_one("#chat_container")
        chat_container.mount(self.selector_widget)
        
        # Добавляем инструкцию
        instruction = Static("\n  Используйте ↑↓ для выбора, Enter для подтверждения, Esc для отмены")
        chat_container.mount(instruction)
        self.selector_instruction = instruction

    # Обновление отображения селектора
    def _update_selector_display(self) -> None:
        if self.selector_widget:
            self.selector_widget.selected_index = self.selector_index
            self.selector_widget.refresh()
    
    # Выбор следующего элемента
    def select_next_item(self) -> None:
        if self.selector_active:
            self.selector_index = (self.selector_index + 1) % len(self.selector_items)
            self._update_selector_display()

    # Выбор предыдущего элемента
    def select_previous_item(self) -> None:
        if self.selector_active:
            self.selector_index = (self.selector_index - 1) % len(self.selector_items)
            self._update_selector_display()

    # Подтверждение выбора
    def confirm_selection(self) -> None:
        if self.selector_active:
            selected_item = self.selector_items[self.selector_index]
            
            # Удаляем виджеты селектора ПЕРЕД вызовом callback
            if self.selector_widget:
                self.selector_widget.remove()
            if self.selector_instruction:
                self.selector_instruction.remove()
            
            # Разблокировка импута
            message_input = self.screen.query_one("#message_input")
            message_input.disabled = False
            message_input.placeholder = "Введите сообщение... (Нажмите Enter для отправки)"
            message_input.focus()
            
            # Вызываем callback если он есть
            if self.selector_callback:
                self.selector_callback(selected_item, self.selector_index)
            
            # Сбрасываем селектор
            self.selector_active = False
            
            # Возвращаем фокус на Input
            self.screen.query_one("#message_input").focus()
    
    # Отмена выбора
    def cancel_selection(self) -> None:
        if self.selector_active:
            # Удаляем виджеты селектора при отмене
            if self.selector_widget:
                self.selector_widget.remove()
            if self.selector_instruction:
                self.selector_instruction.remove()

            # Разблокировка импута
            message_input = self.screen.query_one("#message_input")
            message_input.disabled = False
            message_input.placeholder = "Введите сообщение... (Нажмите Enter для отправки)"
            message_input.focus()
            
            # Сбрасываем селектор ПЕРЕД показом сообщения
            self.selector_active = False
            
            # Показываем сообщение об отмене
            self.screen.update_chat_display("❌ Выбор отменен")
            
            # Возвращаем фокус на Input
            self.screen.query_one("#message_input").focus()
