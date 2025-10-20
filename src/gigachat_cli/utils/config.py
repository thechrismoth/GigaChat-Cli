from pathlib import Path
import json

class Config:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.config_file = Path.home() / ".gigachat" / "config.json"
            self.config_file.parent.mkdir(exist_ok=True)
            
            if not self.config_file.exists():
                self._create_default_config()
            
            self._initialized = True
    
    # Создаем конфиг по умолчанию
    def _create_default_config(self):
        config = {"model": "GigaChat-2"}
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    # Получаем модель из конфига
    def get_model(self) -> str:
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config["model"]
    
    # Устанавливаем новую модель
    def set_model(self, model: str):
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        config["model"] = model
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
