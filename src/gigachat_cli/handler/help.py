from textual.widgets import Input

# Хендлер обработки команды /file
class HelpHandler:
    async def handle(self, user_text: str, input_field: Input, screen):
        if user_text.strip() != '/help':
            return False

        help_text = """
**Доступные команды:**

- `/model` - Выбор модели GigaChat
- `/file`  - Загрузка и работа с файлами
- `/help`  - Показать эту справку
- `/exit`  - Выйти из приложения

**Управление:**

- `Tab`/`Shift+Tab` - навигация по автодополнению
- `↑`/`↓` - навигация в селекторах  
- `Enter` - подтвердить выбор
- `Esc` - отмена
"""
        screen.clear_chat_display()
        screen.update_chat_display(help_text)
        input_field.value = ""
        return True
