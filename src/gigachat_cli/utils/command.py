import asyncio
import shlex
import os
from pathlib import Path
from typing import Tuple, Optional


class CommandUtils:
    """Утилита для выполнения системных команд и работы с файловой системой"""
    
    def __init__(self):
        """Инициализация утилиты команд"""
        self.current_directory = Path.cwd()
        # Список команд, работающих с файловой системой
        self.file_commands = ['cd', 'ls', 'cp', 'mv', 'rm', 'mkdir', 'cat', 'touch', 'find', 'grep']
    
    async def execute_system_command(self, command: str) -> Tuple[bool, str, int]:
        """
        Выполнение системной команды и возврат результата
        
        Args:
            command: Строка команды для выполнения
            
        Returns:
            Tuple[bool, str, int]: (успех, вывод, код возврата)
        """
        if not command.strip():
            return False, "Пустая команда", 1
        
        try:
            # Обрабатываем команду cd отдельно
            if command.strip().startswith('cd '):
                return await self._handle_cd_command(command)
            
            # Разбираем команду с поддержкой флагов
            args = shlex.split(command)
            
            if not args:
                return False, "Не удалось разобрать команду", 1
            
            # Создаем подпроцесс в текущей директории
            process = await asyncio.create_subprocess_exec(
                args[0],
                *args[1:],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.current_directory
            )
            
            # Читаем вывод команды
            stdout, stderr = await process.communicate()
            return_code = await process.wait()
            
            # Формируем результат выполнения
            output_lines = []
            
            if stdout:
                output_lines.append(stdout.decode('utf-8', errors='replace'))
            
            if stderr:
                output_lines.append(stderr.decode('utf-8', errors='replace'))
            
            output_text = "\n".join(output_lines)
            
            return return_code == 0, output_text, return_code
            
        except FileNotFoundError:
            return False, f"Команда '{args[0]}' не найдена", 1
        except Exception as e:
            return False, f"Ошибка выполнения: {e}", 1
    
    async def _handle_cd_command(self, command: str) -> Tuple[bool, str, int]:
        """
        Обработка команды смены директории
        
        Args:
            command: Команда cd с аргументами
            
        Returns:
            Tuple[bool, str, int]: (успех, сообщение, код возврата)
        """
        try:
            args = shlex.split(command)
            if len(args) < 2:
                return False, "cd: требуется аргумент - директория", 1
            
            target_dir = args[1]
            
            # Если путь относительный, делаем его абсолютным относительно текущей директории
            if not os.path.isabs(target_dir):
                target_path = self.current_directory / target_dir
            else:
                target_path = Path(target_dir)
            
            # Разрешаем путь (обрабатываем .., ., ~ и т.д.)
            resolved_path = target_path.resolve()
            
            # Проверяем существование директории
            if not resolved_path.exists():
                return False, f"cd: {target_dir}: Директория не существует", 1
            
            if not resolved_path.is_dir():
                return False, f"cd: {target_dir}: Не является директорией", 1
            
            # Меняем текущую директорию
            self.current_directory = resolved_path
            
            return True, f"Директория изменена на: {resolved_path}", 0
            
        except Exception as e:
            return False, f"cd: ошибка: {e}", 1
    
    def get_current_directory(self) -> Path:
        """
        Получение текущей рабочей директории
        
        Returns:
            Path: Текущая директория
        """
        return self.current_directory
    
    @staticmethod
    def is_terminal_command(text: str) -> Tuple[bool, Optional[str]]:
        """
        Проверка является ли текст терминальной командой
        
        Args:
            text: Текст для проверки
            
        Returns:
            Tuple[bool, Optional[str]]: (является командой, команда без префикса)
        """
        text = text.strip()
        if text.startswith('!'):
            return True, text[1:].strip()
        return False, None
    
    @staticmethod
    def format_command_output(output: str, success: bool, return_code: int) -> str:
        """
        Форматирование вывода команды в Markdown
        
        Args:
            output: Вывод команды
            success: Успешность выполнения
            return_code: Код возврата
            
        Returns:
            str: Отформатированный вывод в Markdown
        """
        status_text = "Выполнено" if success else f"Завершено с кодом {return_code}"
        
        return (
            f"```\n{output}\n```\n"
            f"**{status_text}**"
        )
    
    def is_file_command(self, command: str) -> bool:
        """
        Проверка является ли команда файловой
        
        Args:
            command: Команда для проверки
            
        Returns:
            bool: True если команда работает с файловой системой
        """
        command_parts = command.split()
        if not command_parts:
            return False
        return command_parts[0] in self.file_commands
