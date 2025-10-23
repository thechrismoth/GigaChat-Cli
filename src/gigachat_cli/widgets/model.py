from textual.widgets import Static
from gigachat_cli.utils.config import Config

class Model(Static):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = Config()
        self.current_model = config.get_model()
    
    def render(self) -> str:
        # Сопоставляем техническое название с человеческим
        model_names = {
            "GigaChat-2": "GigaChat 2 Lite",
            "GigaChat-2-Pro": "GigaChat 2 Pro",
            "GigaChat-2-Max": "GigaChat 2 Max",
        }
        display_name = model_names.get(self.current_model, self.current_model)
        return f"Модель: {display_name}"
