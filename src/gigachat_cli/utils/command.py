import asyncio
import shlex
import os
from pathlib import Path
from typing import Tuple, Optional

class CommandUtils:
    
    def __init__(self):
        self.current_directory = Path.cwd()
        # Список команд, работающих с файловой системой
        self.file_commands = ['cd', 'ls', 'cp', 'mv', 'rm', 'mkdir', 'cat', 'touch', 'find', 'grep']
    
    #Выполняем системную команду и возвращаем результат 
    async def execute_system_command(self, command: str) -> Tuple[bool, str, int]: 
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
            
            # Читаем вывод
            stdout, stderr = await process.communicate()
            return_code = await process.wait()
            
            # Формируем результат
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
    
    # Отдельно обрабатываем команду cd
    async def _handle_cd_command(self, command: str) -> Tuple[bool, str, int]:
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
    
    #Возвращаем текущую дирректорию
    def get_current_directory(self) -> Path:
        return self.current_directory
    
    #Провека являетя ли текст консольной командой
    @staticmethod
    def is_terminal_command(text: str) -> Tuple[bool, Optional[str]]: 
        text = text.strip()
        if text.startswith('!'):
            return True, text[1:].strip()
        return False, None
    
    # Формируем вывод команды в MD
    @staticmethod
    def format_command_output(output: str, success: bool, return_code: int) -> str: 
        status_text = "Выполнено" if success else f"Завершено с кодом {return_code}"
        
        return (
            f"```\n{output}\n```\n"
            f"**{status_text}**"
        )
    
    def is_file_command(self, command: str) -> bool:
        """Проверяет, является ли команда файловой"""
        command_parts = command.split()
        if not command_parts:
            return False
        return command_parts[0] in self.file_commands
