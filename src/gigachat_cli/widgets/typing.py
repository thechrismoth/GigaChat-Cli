import asyncio
from textual.widgets import Static

class TypingIndicator(Static):
    """Индикатор набора сообщения"""
    
    def __init__(self):
        super().__init__("")
        self._is_animating = False
        self._animation_task = None
    
    def on_mount(self) -> None:
        self.add_class("typing")
        self.start_animation()
    
    def start_animation(self) -> None:
        """Запускает анимацию"""
        if not self._is_animating:
            self._is_animating = True
            self._animation_task = asyncio.create_task(self._animate_typing())
    
    async def _animate_typing(self) -> None:
        dots = ["", ".", "..", "..."]
        while self._is_animating and self.has_class("typing"):
            for dot in dots:
                if not self._is_animating:
                    break
                self.update(f"GigaChat набирает сообщение{dot}")
                await asyncio.sleep(0.5)
    
    def stop_animation(self) -> None:
        """Останавливает анимацию"""
        self._is_animating = False
        if self._animation_task and not self._animation_task.done():
            self._animation_task.cancel()
        self.update("")
    
    def on_unmount(self) -> None:
        self.stop_animation()
