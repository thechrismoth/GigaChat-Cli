from textual.app import App

from gigachat_cli.screens.start import MenuApp

# Основное приложение
class Main(App):   
    def on_mount(self) -> None:
        # Устанавливаем стартовый экран при запуске
        self.push_screen(MenuApp()) 
