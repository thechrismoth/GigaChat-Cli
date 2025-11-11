from textual.widgets import Static

class Recommend(Static):
    def render(self) -> str:
        recommend  = '''
  Советы для начала работы:
  1. Задавайте вопросы, редактируйте файлы или запускайте команды
  2. Будьте конкретны для получения наилучших результатов
  3. /help для получения дополнительной информации

        '''
       
        return recommend
