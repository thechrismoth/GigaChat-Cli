class ListUtils:
    """Утилита для работы со списком команд и их фильтрации"""
    
    def __init__(self):
        """Инициализация утилиты команд"""
        self.commands = {
            "exit": "Выйти из приложения",
            "model": "Выбор модели GigaChat",
            "help": "Показать справку по командам",
            "menu":  "Возврат в меню"
        }

    def get_filtered_commands(self, text: str) -> list[str]:
        """
        Получение отфильтрованного списка команд
        
        Args:
            text: Текст для фильтрации команд
            
        Returns:
            list[str]: Список отфильтрованных команд с префиксом /
        """
        if not text.startswith('/'):
            return []

        search_text = text[1:].lower()
        
        # Возвращаем все подходящие команды (без ограничения)
        filtered = [f"/{cmd}" for cmd in self.commands.keys() if cmd.startswith(search_text)]
        filtered.sort()
        return filtered
    
    def get_commands_with_descriptions(self, text: str) -> list[tuple[str, str]]:
        """
        Получение отфильтрованного списка команд с описаниями
        
        Args:
            text: Текст для фильтрации команд
            
        Returns:
            list[tuple[str, str]]: Список кортежей (команда, описание)
        """
        if not text.startswith('/'):
            return []

        search_text = text[1:].lower()
        
        # Возвращаем все подходящие команды с описаниями
        filtered = [
            (f"/{cmd}", desc) 
            for cmd, desc in self.commands.items() 
            if cmd.startswith(search_text)
        ]
        filtered.sort(key=lambda x: x[0])
        return filtered
    
    def should_show_commands(self, text: str) -> bool:
        """
        Проверка необходимости показа автодополнения команд
        
        Args:
            text: Текст из поля ввода
            
        Returns:
            bool: True если нужно показывать автодополнение команд
        """
        return text.startswith('/')
