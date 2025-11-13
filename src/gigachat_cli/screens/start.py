import importlib.resources

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import ListView, ListItem, Label
from textual.containers import Container

from gigachat_cli.screens.chat import ChatScreen
from gigachat_cli.screens.help import HelpScreen
from gigachat_cli.widgets.banner import Banner


class MenuApp(Screen):
    """Главный экран меню приложения"""
    
    CSS = importlib.resources.files("gigachat_cli.styles").joinpath("start.css").read_text()  

    def compose(self) -> ComposeResult:
        """
        Композиция виджетов главного меню
        
        Returns:
            ComposeResult: Контейнер с баннером и списком пунктов меню
        """
        yield Container(
            Banner(),
            Container(
                ListView(
                    ListItem(Label("🚀 Начать использование", classes="menu-item"), id="start", classes="menu-button"),
                    ListItem(Label("❓ Помощь и инструкции", classes="menu-item"), id="help", classes="menu-button"),
                    ListItem(Label("🚪 Выход", classes="menu-item"), id="exit", classes="menu-button"),
                    classes="menu-list"
                ),
                classes="buttons-container"
            ),
            classes="main-container"
        )
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """
        Обработчик выбора пункта меню
        
        Args:
            event: Событие выбора элемента списка
        """
        choice = event.item.id
        if choice == "start":
            # Переход к экрану чата
            self.app.push_screen(ChatScreen())  
        elif choice == "help":
            # Переход к экрану справки
            self.app.push_screen(HelpScreen())
        elif choice == "exit":
            # Выход из приложения
            self.app.exit()

    def on_mount(self) -> None:
        """Инициализация при монтировании экрана меню"""
        # Установка фокуса на список меню для навигации
        self.query_one(ListView).focus()
    
    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """
        Обработчик подсветки пунктов меню
        
        Args:
            event: Событие подсветки элемента списка
        """
        # Сброс активного класса у всех пунктов меню
        list_view = self.query_one(ListView)
        for item in list_view.children:
            item.remove_class("active")
            
        # Установка активного класса для подсвеченного пункта
        if event.item:
            event.item.add_class("active")
