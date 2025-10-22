class ListUtils:

    def __init__(self):
        self.commands = ["exit", "file", "model"]
        self.model_names = {
            "GigaChat-2": "GigaChat 2 Lite",
            "GigaChat-2-Pro": "GigaChat 2 Pro", 
            "GigaChat-2-Max": "GigaChat 2 Max",
        }

    def get_filtered_commands(self, text: str) -> list[str]:
        if not text.startswith('/'):
            return []

        search_text = text[1:].lower()

        # Если начинается с /model, показываем модели вместо команд
        if text.startswith('/model'):
            model_search = text[7:].lower()  # Убираем "/model "
            return [f"model {key}" for key in self.model_names.keys() 
                   if key.lower().startswith(model_search)]

        # Иначе показываем обычные команды
        return [cmd for cmd in self.commands if cmd.startswith(search_text)]
    
    def should_show_commands(self, text: str) -> bool:
        return text.startswith('/')

    def get_model_display_name(self, model_key: str) -> str:
        # Возвращаем имя модели
        return self.model_names.get(model_key, model_key)
