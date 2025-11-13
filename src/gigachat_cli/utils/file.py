from pathlib import Path
import os
from typing import List, Tuple


class FileUtils:
    """Утилита для работы с файловой системой и автодополнением файлов"""
    
    def __init__(self, command_utils):
        """
        Инициализация утилиты файлов
        
        Args:
            command_utils: Утилита команд для получения текущей директории
        """
        self.command_utils = command_utils
        # Список команд, работающих с файловой системой
        self.file_commands = ['cd', 'ls', 'cp', 'mv', 'rm', 'mkdir', 'cat', 'touch', 'find', 'grep']
    
    def should_show_files(self, text: str) -> bool:
        """
        Проверка необходимости показа автодополнения файлов
        
        Args:
            text: Текст из поля ввода
            
        Returns:
            bool: True если нужно показывать автодополнение файлов
        """
        if not text.strip().startswith('!'):
            return False
        
        # Разбираем команду на части
        parts = text.strip().split()
        if len(parts) < 1:
            return False
        
        command = parts[0][1:]  # Убираем префикс !
        
        # Проверяем, является ли команда файловой
        if command not in self.file_commands:
            return False
        
        # Показываем файлы если есть пробел после команды или есть аргументы
        return len(parts) >= 2 or text.endswith(' ')
    
    def get_files_for_completion(self, text: str) -> Tuple[List[str], str, str]:
        """
        Получение списка файлов для автодополнения
        
        Args:
            text: Текст команды для автодополнения
            
        Returns:
            Tuple[List[str], str, str]: (список файлов, полная команда, текущий путь)
        """
        parts = text.strip().split()
        if len(parts) < 1:
            return [], text, ""
        
        current_dir = self.command_utils.get_current_directory()
        
        # Обработка случая когда есть только команда с пробелом (например: "!ls ")
        if len(parts) == 1 and text.endswith(' '):
            search_pattern = ""
            base_path = current_dir
            last_part = ""
        elif len(parts) >= 2:
            last_part = parts[-1]
            
            # Определение базового пути для поиска
            if last_part.startswith('/'):
                # Абсолютный путь - начинаем с корня
                base_path = Path('/')
                search_pattern = last_part[1:]  # Убираем начальный слеш
            elif '/' in last_part:
                # Относительный путь с поддиректориями
                path_parts = last_part.split('/')
                search_dir = '/'.join(path_parts[:-1])
                search_pattern = path_parts[-1] or ""
                
                base_path = current_dir / search_dir
            else:
                # Простой поиск в текущей директории
                search_pattern = last_part
                base_path = current_dir
        else:
            return [], text, str(current_dir)
        
        # Проверка существования базового пути
        if not base_path.exists() or not base_path.is_dir():
            return [], text, str(base_path)
        
        try:
            # Получение всех файлов и директорий (включая скрытые)
            all_items = []
            for item in base_path.iterdir():
                # Если search_pattern пустой, показываем все файлы
                if not search_pattern:
                    all_items.append(item.name)
                else:
                    # Фильтрация по паттерну (показываем все совпадения)
                    if item.name.startswith(search_pattern):
                        all_items.append(item.name)
            
            # Сортировка: сначала директории, потом файлы
            def sort_key(item):
                item_path = base_path / item
                return (0 if item_path.is_dir() else 1, item.lower())
            
            all_items.sort(key=sort_key)
            
            return all_items, text, str(base_path)
            
        except (PermissionError, OSError):
            return [], text, str(base_path)
