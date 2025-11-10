from textual.widgets import Static
from textual.reactive import reactive

class SelectorWidget(Static):
    """Виджет для интерактивного выбора с цветным выделением"""
    
    items = reactive([])
    selected_index = reactive(0)
    
    def render(self) -> str:
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
