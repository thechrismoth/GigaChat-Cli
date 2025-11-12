class ListUtils:

    def __init__(self):
        self.commands = {
            "exit": "Выйти из приложения",
            "model": "Выбор модели GigaChat",
            "help": "Показать справку по командам"
        }

    def get_filtered_commands(self, text: str) -> list[str]:
        if not text.startswith('/'):
            return []

        search_text = text[1:].lower()
        
        # Возвращаем ВСЕ подходящие команды (без ограничения)
        filtered = [f"/{cmd}" for cmd in self.commands.keys() if cmd.startswith(search_text)]
        filtered.sort()
        return filtered
    
    def get_commands_with_descriptions(self, text: str) -> list[tuple[str, str]]:
        if not text.startswith('/'):
            return []

        search_text = text[1:].lower()
        
        # Возвращаем ВСЕ подходящие команды (без ограничения)
        filtered = [
            (f"/{cmd}", desc) 
            for cmd, desc in self.commands.items() 
            if cmd.startswith(search_text)
        ]
        filtered.sort(key=lambda x: x[0])
        return filtered
    
    def should_show_commands(self, text: str) -> bool:
        return text.startswith('/')
