from textual.widgets import Static
from textual.reactive import reactive


class SelectorWidget(Static):
    """Виджет для интерактивного выбора с цветовым выделением"""

    items = reactive([])
    selected_index = reactive(0)
    
    def render(self) -> str:
        """
        Рендеринг списка элементов с выделением выбранного
        
        Returns:
            str: Отформатированный список элементов с цветовым выделением
        """
        if not self.items:
            return ""
            
        lines = []
        for i, item in enumerate(self.items):
            if i == self.selected_index:
                # Выделенный элемент - используем правильный синтаксис Textual
                lines.append(f"➤ [green]{item}[/]")
            else:
                lines.append(f"  {item}")
        
        return "\n".join(lines)
