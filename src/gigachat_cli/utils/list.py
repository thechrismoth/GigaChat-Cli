class ListUtils:

    def __init__(self):
        self.commands = ["exit", "file", "model"]

    def get_filtered_commands(self, text: str) -> list[str]:
        if not text.startswith('/'):
            return []

        search_text = text[1:].lower()

        # Показываем только обычные команды (возвращаем с / для правильного дополнения)
        return [f"/{cmd}" for cmd in self.commands if cmd.startswith(search_text)]
    
    def should_show_commands(self, text: str) -> bool:
        return text.startswith('/')
