import asyncio
from textual.widgets import Static


class TypingIndicator(Static):
    """Индикатор набора сообщения"""
    
    def __init__(self):
        """
        Инициализация индикатора набора
        
        Args:
            *args: Аргументы родительского класса
            **kwargs: Ключевые аргументы родительского класса
        """
        super().__init__(".")
        self._is_animating = False
        self._animation_task = None
    
    def on_mount(self) -> None:
        """Запуск анимации при монтировании виджета"""
        self.add_class("typing")
        self._is_animating = True
        self._animation_task = asyncio.create_task(self._animate_typing())
    
    async def _animate_typing(self) -> None:
        """Анимация точек индикатора"""
        dots = [".", "..", "...", ""]
        index = 0
        while self._is_animating and self.has_class("typing"):
            self.update(dots[index])
            index = (index + 1) % len(dots)
            await asyncio.sleep(0.4)
    
    def stop_animation(self) -> None:
        """Остановка анимации индикатора"""
        self._is_animating = False
        if self._animation_task and not self._animation_task.done():
            self._animation_task.cancel()
        self.update("")
    
    def on_unmount(self) -> None:
        """Очистка ресурсов при размонтировании"""
        self.stop_animation()
