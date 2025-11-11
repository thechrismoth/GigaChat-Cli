class ListUtils:

    def __init__(self):
        self.commands = {
            "exit": "Выйти из приложения",
            "file": "Работа с файлами", 
            "model": "Выбор модели GigaChat",
            "help": "Показать справку по командам"
        }

    def get_filtered_commands(self, text: str) -> list[str]:
        if not text.startswith('/'):
            return []

        search_text = text[1:].lower()
        
        # Возвращаем команды для автодополнения (только названия)
        return [f"/{cmd}" for cmd in self.commands.keys() if cmd.startswith(search_text)]
    
    def get_commands_with_descriptions(self, text: str) -> list[tuple[str, str]]:
        """Возвращает список (команда, описание) для отображения"""
        if not text.startswith('/'):
            return []

        search_text = text[1:].lower()
        
        return [
            (f"/{cmd}", desc) 
            for cmd, desc in self.commands.items() 
            if cmd.startswith(search_text)
        ]
    
    def should_show_commands(self, text: str) -> bool:
        return text.startswith('/')
