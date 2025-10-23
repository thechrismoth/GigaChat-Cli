import re

from textual.widgets import TextArea

from gigachat_cli.utils.config import Config

# Хендлер обработки команды /model
class ModelHandler:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.model_names = {
            "GigaChat-2": "GigaChat 2 Lite",
            "GigaChat-2-Pro": "GigaChat 2 Pro", 
            "GigaChat-2-Max": "GigaChat 2 Max",
        }

    async def handle(self, user_text: str, text_area: TextArea, screen):
        if not user_text.lower().startswith('/model'):
            return False

        if user_text.strip() == '/model':
            model_list = "\n\n".join([f"• {key}: {value}" for key, value in self.model_names.items()]) 
            screen.user_inputs.append(("Система", f"**Доступные модели:**\n\n{model_list}"))

            screen.update_chat_display()
        
            # Очищаем поле ввода
            text_area = screen.query_one("#message_input", TextArea)
            text_area.text = ""
            text_area.focus()

            return True
        else:
            # Если есть аргументы - обрабатываем выбор модели
            match = re.match(r'/model\s+(.+)', user_text) 
            if match:
                model_key = match.group(1).strip()
                model_names = self.model_names

                if model_key in model_names:
                    self.cfg.set_model(model_key)
                    screen.user_inputs.append(("Система", f"Выбрана модель: {model_names[model_key]}"))
                    
                else:
                    screen.user_inputs.append(("Система", f"Модель '{model_key}' не найдена. Используйте /model для просмотра списка."))
                
                screen._update_model_display()
                screen.update_chat_display()

                # Очищаем поле ввода
                text_area = screen.query_one("#message_input", TextArea)
                text_area.text = ""
                text_area.focus()

                return True

        return False

