from textual.app import App

from gigachat_cli.screens.start import MenuApp


class Main(App):
    """Основной класс приложения GigaChat CLI"""
    
    def on_mount(self) -> None:
        """
        Инициализация приложения при монтировании
        
        Устанавливает стартовый экран меню при запуске приложения
        """
        self.push_screen(MenuApp())
