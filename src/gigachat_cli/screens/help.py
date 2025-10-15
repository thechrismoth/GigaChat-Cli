import importlib.resources

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import VerticalScroll
from textual.widgets import Markdown
from textual import events

from gigachat_cli.widgets.banner import Banner

HELP_CONTENT = """
# 🚀 Руководство пользователя GigaChat

## ⚙️ Начало работы

Перед запуском приложения установите API-ключ в системе:

```Bash
export GIGACHAT_API_KEY="YOUR_API_KEY"
```
## ⌨️ Управление вводом

**Горячие клавиши:**
- `Ctrl+Shift+V` - вставить текст из буфера обмена
- `Enter` - переход на новую строку в тексте  
- `Shift+Enter` - отправить сообщение
- `Ctrl+Q` - выход из приложения

## 💡 Как работать с приложением

1. **Начните диалог** - просто введите текст в поле ввода
2. **Форматируйте текст** - используйте Enter для переноса строк
3. **Отправляйте сообщения** - нажмите Shift+Enter когда текст готов
4. **![command] [key]** - используйте ! для работы с терминальными командами
5. **/file [file_name] [prompt]** - используйте коману /file для отправки вашего файла в GigaChat
6. **/exit** - используйте команду /exit для завершения работы приложения

---
*Для возврата в меню нажмите Escape*
"""

class HelpScreen(Screen):
    CSS = importlib.resources.files("gigachat_cli.styles").joinpath("help.css").read_text()


    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            Banner(),
            Markdown(HELP_CONTENT)
        )
    
    #обработка комбинации для отправки сообщения 
    def on_key(self, event: events.Key) -> None:
         if event.key == "escape":
            self.app.pop_screen()

   
