from pathlib import Path
import json


class Config:
    """Класс для управления конфигурацией приложения"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Реализация singleton паттерна"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Инициализация конфигурации"""
        if not self._initialized:
            # Путь к файлу конфигурации в домашней директории пользователя
            self.config_file = Path.home() / ".gigachat" / "config.json"
            # Создание директории конфигурации если не существует
            self.config_file.parent.mkdir(exist_ok=True)
            
            # Создание конфигурации по умолчанию если файл не существует
            if not self.config_file.exists():
                self._create_default_config()
            
            self._initialized = True
    
    def _create_default_config(self):
        """
        Создание конфигурации по умолчанию
        """
        config = {"model": "GigaChat-2"}
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def get_model(self) -> str:
        """
        Получение текущей модели из конфигурации
        
        Returns:
            str: Название текущей модели
        """
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config["model"]
    
    def set_model(self, model: str):
        """
        Установка новой модели в конфигурацию
        
        Args:
            model: Название модели для установки
        """
        # Чтение текущей конфигурации
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Обновление модели
        config["model"] = model
        
        # Сохранение обновленной конфигурации
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
