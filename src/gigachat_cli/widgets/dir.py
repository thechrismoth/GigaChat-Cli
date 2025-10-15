import os
from textual.widgets import Static

class Dir(Static):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_dir = os.path.abspath(os.curdir)
    
    def render(self) -> str:
        return f"📁 Директория: {self.current_dir}"
