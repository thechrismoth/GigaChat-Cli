import os

from textual.widgets import Static

class Dir(Static):
    def render(self) -> str:
        current_dir = os.path.abspath(os.curdir)
        return f"📁 Директория: {current_dir}" 
    

 
