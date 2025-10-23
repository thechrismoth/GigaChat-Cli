import importlib.resources

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import ListView, ListItem, Label
from textual.containers import Container

from gigachat_cli.screens.chat import ChatScreen
from gigachat_cli.screens.help import HelpScreen
from gigachat_cli.widgets.banner import Banner

class MenuApp(Screen):
    CSS = importlib.resources.files("gigachat_cli.styles").joinpath("start.css").read_text()  

    def compose(self) -> ComposeResult:
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
        choice = event.item.id
        if choice == "start":
            self.app.switch_screen(ChatScreen())  
        elif choice == "help":
            self.app.push_screen(HelpScreen())
        elif choice == "exit":
            self.app.exit()

    def on_mount(self) -> None:
        # Устанавливаем фокус на ListView
        self.query_one(ListView).focus()
    
    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        # Обновляем классы при изменении выделения
        list_view = self.query_one(ListView)
        for item in list_view.children:
            item.remove_class("active")
        if event.item:
            event.item.add_class("active")
