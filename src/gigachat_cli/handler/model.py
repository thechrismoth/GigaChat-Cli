from textual.widgets import Input

from gigachat_cli.utils.config import Config


class ModelHandler:
    """Обработчик команды /model для выбора модели GigaChat"""
    
    def __init__(self, cfg: Config, screen=None):
        """
        Инициализация обработчика моделей
        
        Args:
            cfg: Конфигурация приложения
            screen: Экран чата для обновления интерфейса
        """
        self.cfg = cfg
        self.screen = screen
        # Сопоставление ключей моделей с читаемыми названиями
        self.model_names = {
            "GigaChat-2": "GigaChat 2 Lite",
            "GigaChat-2-Pro": "GigaChat 2 Pro", 
            "GigaChat-2-Max": "GigaChat 2 Max",
        }

    async def handle(self, user_text: str, input_field: Input, screen) -> bool:
        """
        Обработка команды выбора модели
        
        Args:
            user_text: Текст сообщения пользователя
            input_field: Поле ввода для управления
            screen: Экран чата для обновления отображения
            
        Returns:
            bool: True если команда обработана, False если нет
        """
        # Проверка что это команда /model
        if not user_text.lower().startswith('/model'):
            return False

        # Обработка команды /model без параметров
        if user_text.strip() == '/model':
            # Показываем селектор с доступными моделями
            model_list = [name for name in self.model_names.values()]
            
            screen.selector_manager.show_selector(
                items=model_list,
                title="Выберите модель:",
                callback=self._on_model_selected
            )
            
            # Очистка поля ввода и возврат фокуса
            input_field.value = ""
            input_field.focus()
            return True
 
        return False

    def _on_model_selected(self, selected_item: str, index: int):
        """
        Callback функция выбора модели из списка
        
        Args:
            selected_item: Выбранное название модели
            index: Индекс выбранного элемента в списке
        """
        # Поиск ключа модели по читаемому названию
        model_key = None
        for key, name in self.model_names.items():
            if name == selected_item:
                model_key = key
                break
        
        if model_key:
            # Установка выбранной модели в конфигурацию
            self.cfg.set_model(model_key)
            
            # Отображение результата выбора пользователю
            self.screen.update_chat_display(f"**Система:** ✅ Выбрана модель: **{selected_item}**")
            # Обновление отображения текущей модели в интерфейсе
            self.screen._update_model_display()
