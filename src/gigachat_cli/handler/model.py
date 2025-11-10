import re

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

        if user_text.strip() == '/model':
            # Добавляем сообщение пользователя
            screen.user_inputs.append(("Вы", user_text))
            
            # Создаем список моделей для селектора (только названия для отображения)
            model_list = [name for name in self.model_names.values()]
            
            # Показываем селектор с callback для обработки выбора
            screen.selector_manager.show_selector(
                items=model_list,
                title="Выберите модель:",
                callback=self._on_model_selected
            )
            
            screen.update_chat_display()
            input_field.value = ""
            input_field.focus()
            return True
        else:
            # Если есть аргументы - обрабатываем выбор модели через текст
            match = re.match(r'/model\s+(.+)', user_text) 
            if match:
                model_key = match.group(1).strip()
                
                if model_key in self.model_names:
                    self.cfg.set_model(model_key)
                    screen.user_inputs.append(("Система", f"Выбрана модель: {self.model_names[model_key]}"))
                else:
                    screen.user_inputs.append(("Система", f"Модель '{model_key}' не найдена. Используйте /model для просмотра списка."))
                
                screen._update_model_display()
                screen.update_chat_display()
                input_field.value = ""
                input_field.focus()
                return True

        return False

    def _on_model_selected(self, selected_item: str, index: int):
        """Callback вызывается когда пользователь выбирает модель из селектора"""
        # Находим ключ модели по названию
        model_key = None
        for key, name in self.model_names.items():
            if name == selected_item:
                model_key = key
                break
        
        if model_key:
            # Устанавливаем выбранную модель
            self.cfg.set_model(model_key)
            
            # Добавляем сообщение о выборе
            self.screen.user_inputs.append(("Система", f"✅ Выбрана модель: **{selected_item}**"))
            self.screen._update_model_display()
            self.screen.update_chat_display()
