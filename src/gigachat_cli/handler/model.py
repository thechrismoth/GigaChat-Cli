from textual.widgets import Input

from gigachat_cli.utils.config import Config

# Хендлер обработки команды /model
class ModelHandler:
    def __init__(self, cfg: Config, screen=None):
        self.cfg = cfg
        self.screen = screen
        self.model_names = {
            "GigaChat-2": "GigaChat 2 Lite",
            "GigaChat-2-Pro": "GigaChat 2 Pro", 
            "GigaChat-2-Max": "GigaChat 2 Max",
        }

    async def handle(self, user_text: str, input_field: Input, screen):
        if not user_text.lower().startswith('/model'):
            return False

        # Чат уже очищен в process_message, просто показываем результат
        
        if user_text.strip() == '/model':
            # Показываем селектор моделей
            model_list = [name for name in self.model_names.values()]
            
            screen.selector_manager.show_selector(
                items=model_list,
                title="Выберите модель:",
                callback=self._on_model_selected
            )
            
            input_field.value = ""
            input_field.focus()
            return True
 
        return False

    # Вызываем Callback когда произведен выбор из списка
    def _on_model_selected(self, selected_item: str, index: int):
        # Находим ключ модели по названию
        model_key = None
        for key, name in self.model_names.items():
            if name == selected_item:
                model_key = key
                break
        
        if model_key:
            # Устанавливаем выбранную модель
            self.cfg.set_model(model_key)
            
            # Показываем результат выбора
            self.screen.update_chat_display(f"**Система:** ✅ Выбрана модель: **{selected_item}**")
            self.screen._update_model_display()
