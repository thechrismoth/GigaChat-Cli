from textual.widgets import Static
from gigachat_cli.utils.config import Config


class Model(Static):
    """Виджет отображения текущей модели GigaChat"""
    
    def __init__(self, *args, **kwargs):
        """
        Инициализация виджета модели
        
        Args:
            *args: Аргументы родительского класса
            **kwargs: Ключевые аргументы родительского класса
        """
        super().__init__(*args, **kwargs)
        config = Config()
        self.current_model = config.get_model()
    
    def render(self) -> str:
        """
        Рендеринг текста с текущей моделью
        
        Returns:
            str: Отформатированная строка с названием модели
        """
        # Сопоставление технических названий с читаемыми
        model_names = {
            "GigaChat-2": "GigaChat 2 Lite",
            "GigaChat-2-Pro": "GigaChat 2 Pro",
            "GigaChat-2-Max": "GigaChat 2 Max",
        }
        display_name = model_names.get(self.current_model, self.current_model)
        return f"Модель: {display_name}"
