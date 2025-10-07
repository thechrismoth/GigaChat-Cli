import asyncio

from textual.widgets import Static

class TypingIndicator(Static):
    """Индикатор набора сообщения"""
    
    def on_mount(self) -> None:
        self.add_class("typing")
        self.animation_task = asyncio.create_task(self.animate_typing())
    
    async def animate_typing(self) -> None:
        dots = ["", ".", "..", "..."]
        while self.has_class("typing"):
            for dot in dots:
                self.update(f"GigaChat печатает{dot}")
                await asyncio.sleep(0.5)
    
    def stop_animation(self) -> None:
        self.remove_class("typing")
        if hasattr(self, 'animation_task'):
            self.animation_task.cancel()

