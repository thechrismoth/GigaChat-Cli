import os
import asyncio
import aiofiles
import re

from pathlib import Path
from typing import List, Dict, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_gigachat.chat_models import GigaChat

from gigachat_cli.utils.config import Config

class GigaChatManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.conversation_history = []
            cls._instance.config = Config()
            cls._instance.project_context = {}
            cls._instance._file_cache = {}  # Кэш для быстрого поиска файлов
        return cls._instance
    
    # Создание экземлпляра GigaChat c текущей выбранной моделью
    def _get_giga_chat_instance(self) -> GigaChat:
        current_model = self.config.get_model()
        
        return GigaChat(
            credentials=os.getenv("GIGACHAT_API_KEY"),
            verify_ssl_certs=False,
            model=current_model,
            scope="GIGACHAT_API_PERS",
            temperature=0.1,
            max_tokens=4000
        )
    
    # Строим индекс всех файлов в проекте для быстрого поиска
    def _build_file_index(self, project_path: str = None) -> Dict[str, str]:
        if not project_path:
            project_path = os.getcwd()
        
        file_index = {}
        
        try:
            for root, dirs, files in os.walk(project_path):
                # Игнорируем служебные директории
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                    '__pycache__', 'node_modules', 'venv', '.git', '.vscode', '.idea'
                ]]
                
                for file in files:
                    if file.startswith('.'):
                        continue
                    
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, project_path)
                    
                    # Сохраняем полный путь и относительный путь
                    file_index[file] = file_path  # по имени файла
                    file_index[relative_path] = file_path  # по относительному пути
                    file_index[file.lower()] = file_path  # по имени в нижнем регистре
            
            return file_index
            
        except Exception as e:
            print(f"Ошибка построения индекса файлов: {e}")
            return {}
    
    # Находим полный путь к файлу в проекте включая поддиректории
    def _find_file_in_project(self, filename: str, project_path: str = None) -> Optional[str]:
        if not project_path:
            project_path = os.getcwd()
        
        # Если индекс еще не построен - строим
        if not hasattr(self, '_file_index') or not self._file_index:
            self._file_index = self._build_file_index(project_path)
        
        # Пробуем разные варианты поиска
        search_patterns = [
            filename,  # точное имя
            filename.lower(),  # в нижнем регистре
            os.path.basename(filename),  # только имя файла
            os.path.basename(filename).lower(),  # только имя в нижнем регистре
        ]
        
        for pattern in search_patterns:
            if pattern in self._file_index:
                found_path = self._file_index[pattern]
                if os.path.exists(found_path):
                    return found_path
        
        # Если не нашли в индексе, ищем рекурсивно
        try:
            for root, dirs, files in os.walk(project_path):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    if file.lower() == filename.lower() or file == filename:
                        return os.path.join(root, file)
                    
                    # Также проверяем частичное совпадение
                    if filename.lower() in file.lower():
                        return os.path.join(root, file)
        except:
            pass
        
        return None
   
    # Загружаем конект проекта
    async def load_file_content(self, file_path: str, max_size: int = 15000) -> Optional[str]:
        try:
            if not os.path.exists(file_path):
                return None
            
            file_size = os.path.getsize(file_path)
            if file_size > max_size:
                return f"[Файл слишком большой: {file_size} байт, лимит: {max_size} байт]"
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return content
                
        except UnicodeDecodeError:
            return "[Бинарный файл или неподдерживаемая кодировка]"
        except Exception as e:
            return f"[Ошибка чтения файла: {str(e)}]"
    
    #Загружаем содержимое нескольких файлов  по их именам
    async def load_multiple_files(self, file_names: List[str], project_path: str = None) -> Dict[str, str]:
        files_content = {}
        
        for file_name in file_names:
            # Находим полный путь к файлу в проекте
            full_path = self._find_file_in_project(file_name, project_path)
            
            if full_path and os.path.exists(full_path):
                content = await self.load_file_content(full_path)
                relative_path = os.path.relpath(full_path, project_path or os.getcwd())
                files_content[relative_path] = content
            else:
                files_content[file_name] = f"[Файл не найден в проекте: {file_name}]"
        
        return files_content
    
    #Извлекаем упоминания файлов из теста с запроом с улучшенным поиском
    def _extract_file_references(self, text: str) -> List[str]:
        # Более умные паттерны для поиска файлов
        patterns = [
            r'(\w+\.py)', r'(\w+\.js)', r'(\w+\.ts)', r'(\w+\.json)', r'(\w+\.md)', r'(\w+\.yaml)', r'(\w+\.yml)',
            r'(\w+\.txt)', r'(\w+\.html)', r'(\w+\.css)', r'(\w+\.xml)', r'(\w+\.java)', r'(\w+\.cpp)', r'(\w+\.h)',
            r'файл[а-я]*\s+["\']?([^"\'\s]+)["\']?',  # "файл chat.py" или "файл 'config.py'"
            r'file\s+["\']?([^"\'\s]+)["\']?',  # "file config.py" или "file 'settings.py'"
            r'([a-zA-Z_][a-zA-Z0-9_]*\.[a-z]+)',  # общий паттерн для имен файлов
        ]
        
        found_files = set()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match and not match.startswith(('.', '/', '\\')):
                    found_files.add(match)
        
        # Также ищем файлы в кавычках и скобках
        quoted_patterns = [
            r'["\']([^"\']+\.[a-z]+)["\']',  # "chat.py" или 'config.json'
            r'\(([^)]+\.[a-z]+)\)',  # (settings.py)
            r'\[([^]]+\.[a-z]+)\]',  # [package.json]
        ]
        
        for pattern in quoted_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match and not match.startswith(('.', '/', '\\')):
                    found_files.add(match)
        
        return list(found_files)
    
    # получаем ответ с контекстом файлов проекта
    async def get_contextual_answer(self, prompt: str, project_path: str = None) -> str:
        if not project_path:
            project_path = os.getcwd()
        
        # Ищем упоминания файлов в запросе
        referenced_files = self._extract_file_references(prompt)
        
        if referenced_files:
            # Загружаем содержимое упомянутых файлов
            files_content = await self.load_multiple_files(referenced_files, project_path)
            
            # Формируем промпт с содержимым файлов
            context_info = "Содержимое файлов проекта:\n\n"
            files_found = False
            
            for file_path, content in files_content.items():
                if not content.startswith('['):  # Если не ошибка
                    context_info += f"--- {file_path} ---\n{content}\n\n"
                    files_found = True
            
            if files_found:
                full_prompt = f"{context_info}\n\nЗапрос пользователя: {prompt}"
                
                system_message = """Ты - опытный разработчик. Тебе предоставлено содержимое файлов проекта. 
                Анализируй конкретный код из этих файлов и давай точные ответы с примерами.
                Цитируй конкретные строки кода из предоставленных файлов.
                Если предлагаешь изменения - покажи конкретный код ДО и ПОСЛЕ."""
                
                return await self._get_answer_with_system(full_prompt, system_message)
        
        # Если файлы не найдены или не упомянуты, используем стандартный анализ
        return await self.get_code_analysis(prompt, project_path)
    
    # Загружаем контекст проекта
    async def load_project_context(self, project_path: str = None) -> Dict:
        if not project_path:
            project_path = os.getcwd()
        
        context = {
            "project_path": project_path,
            "file_structure": [],
            "key_files": {},
            "dependencies": []
        }
        
        try:
            # Сбрасываем индекс при загрузке нового контекста
            self._file_index = self._build_file_index(project_path)
            
            for root, dirs, files in os.walk(project_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                    '__pycache__', 'node_modules', 'venv', '.git'
                ]]
                
                for file in files:
                    if file.startswith('.'):
                        continue
                        
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, project_path)
                    
                    context["file_structure"].append(relative_path)
                    
                    if self._is_key_file(file) and os.path.getsize(file_path) < 10000:
                        try:
                            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                                content = await f.read()
                                context["key_files"][relative_path] = content[:5000]
                        except:
                            context["key_files"][relative_path] = "[binary or unreadable file]"
            
            return context
            
        except Exception as e:
            print(f"Ошибка загрузки контекста проекта: {e}")
            return context
    
    # Определяем является ли файл ключевым для проекта
    def _is_key_file(self, filename: str) -> bool:
        key_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.json', '.yaml', '.yml', 
            '.md', '.txt', '.html', '.css', '.xml', '.java', '.cpp', '.h'
        }
        key_files = {
            'Dockerfile', 'docker-compose.yml', '.env.example', 'README.md', 
            'config.py', 'settings.py', 'package.json', 'requirements.txt',
            'pyproject.toml', 'setup.py', 'Makefile', 'CMakeLists.txt'
        }
        
        ext = os.path.splitext(filename)[1].lower()
        return ext in key_extensions or filename in key_files
    
    #Специализированный метод для анализа кода
    async def get_code_analysis(self, prompt: str, project_path: str = None) -> str:
        context = await self.load_project_context(project_path)
        
        system_message = """Ты - опытный разработчик-ассистент. Анализируй код проекта и давай конкретные, 
        практические советы. Фокусируйся на:
        1. Качестве кода и лучших практиках
        2. Возможных ошибках и уязвимостях
        3. Оптимизации производительности
        4. Архитектурных улучшениях
        
        Будь конкретен и приводи примеры исправлений."""
        
        context_info = f"Структура проекта ({len(context['file_structure'])} файлов):\n"
        context_info += "\n".join(context['file_structure'][:25])  # Показываем первые 25 файлов
        
        if len(context['file_structure']) > 25:
            context_info += f"\n... и еще {len(context['file_structure']) - 25} файлов"
        
        context_info += "\n\n"
        
        if context["key_files"]:
            context_info += "Ключевые файлы:\n"
            for file, content in list(context["key_files"].items())[:5]:
                context_info += f"\n--- {file} ---\n{content[:1000]}\n"
        
        full_prompt = f"{context_info}\n\nЗапрос: {prompt}"
        
        return await self._get_answer_with_system(full_prompt, system_message)
    
    # Обьяснение кода на естественном языке
    async def explain_code(self, code: str, language: str = "python") -> str:
        system_message = f"""Ты - преподаватель программирования. Объясни этот {language} код простым языком:
        1. Что делает этот код?
        2. Как он работает пошагово?
        3. Какие ключевые конструкции используются?
        4. Есть ли потенциальные проблемы?"""
        
        return await self._get_answer_with_system(f"Код для объяснения:\n```{language}\n{code}\n```", system_message)
    
    # Предлагаем рефакторинг кода
    async def refactor_suggestion(self, code: str, language: str = "python") -> str:
        system_message = f"""Ты - senior разработчик. Проанализируй этот {language} код и предложи улучшения:
        1. Улучшение читаемости
        2. Оптимизация производительности  
        3. Следование best practices
        4. Устранение code smells
        
        Покажи конкретные примеры до/после."""
        
        return await self._get_answer_with_system(f"Код для рефакторинга:\n```{language}\n{code}\n```", system_message)
    
    # Внутренний метод запросов с сообщениями
    async def _get_answer_with_system(self, prompt: str, system_message: str) -> str:
        giga = self._get_giga_chat_instance()
        
        messages = self.conversation_history.copy()
        messages.insert(0, SystemMessage(content=system_message))
        messages.append(HumanMessage(content=prompt))
        
        try:
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(None, giga.invoke, messages)
            
            # Сохраняем только пользовательский промпт и ответ (без system message)
            self.conversation_history.append(HumanMessage(content=prompt))
            self.conversation_history.append(AIMessage(content=res.content))
            
            # Ограничиваем историю
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            return res.content
            
        except Exception as e:
            current_model = self.config.get_model()
            error_msg = f"Ошибка при обращении к API (модель: {current_model}): {str(e)}"
            raise Exception(error_msg)
    
    # Основной метод для получания ответа
    async def get_answer(self, prompt: str, clear_history: bool = False) -> str:
        if clear_history:
            self.conversation_history.clear()
            return "История диалога очищена"
        
        # Автоматически определяем тип запроса
        if any(keyword in prompt.lower() for keyword in ['анализ', 'проект', 'project', 'структур']):
            return await self.get_code_analysis(prompt)
        
        elif any(keyword in prompt.lower() for keyword in ['объясни', 'explain', 'как работает']):
            code_blocks = self._extract_code_blocks(prompt)
            if code_blocks:
                return await self.explain_code(code_blocks[0], self._detect_language(prompt))
        
        elif any(keyword in prompt.lower() for keyword in ['рефакторинг', 'refactor', 'улучши код']):
            code_blocks = self._extract_code_blocks(prompt)
            if code_blocks:
                return await self.refactor_suggestion(code_blocks[0], self._detect_language(prompt))
        
        # Для запросов с упоминанием файлов используем контекстный ответ
        elif self._extract_file_references(prompt):
            return await self.get_contextual_answer(prompt)
        
        # Стандартный запрос
        return await self._get_answer_with_system(prompt, "Ты - полезный AI-ассистент для разработчиков.")
    
    # Извлекаем блоки кода из текста
    def _extract_code_blocks(self, text: str) -> List[str]:
        import re
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', text, re.DOTALL)
        return code_blocks

    # Определяем ЯП из текста
    def _detect_language(self, text: str) -> str:

        if 'python' in text.lower() or '.py' in text:
            return 'python'
        elif 'javascript' in text.lower() or 'js' in text:
            return 'javascript'
        elif 'typescript' in text.lower() or 'ts' in text:
            return 'typescript'
        else:
            return 'python'
    
    def clear_history(self) -> str:
        self.conversation_history.clear()
        return "История диалога очищена"
    
    def get_current_model(self) -> str:
        return self.config.get_model()
    
    def get_conversation_stats(self) -> Dict:
        """Статистика текущей сессии"""
        user_messages = sum(1 for msg in self.conversation_history if isinstance(msg, HumanMessage))
        ai_messages = sum(1 for msg in self.conversation_history if isinstance(msg, AIMessage))
        
        return {
            "total_messages": len(self.conversation_history),
            "user_messages": user_messages,
            "ai_messages": ai_messages,
            "current_model": self.get_current_model()
        }

# Создаем инстанс
chat_manager = GigaChatManager()

# Функции для обратной совместимости
async def get_answer(prompt: str, clear_history: bool = False) -> str:
    return await chat_manager.get_answer(prompt, clear_history)

# Очистка истории
def clear_chat_history() -> str:
    return chat_manager.clear_history()

# Получение текущей модели
def get_current_model() -> str:
    return chat_manager.get_current_model()

# Новые функции для работы с кодом
async def analyze_project(prompt: str, project_path: str = None) -> str:
    return await chat_manager.get_code_analysis(prompt, project_path)

async def explain_code(code: str, language: str = "python") -> str:
    return await chat_manager.explain_code(code, language)

async def refactor_code(code: str, language: str = "python") -> str:
    return await chat_manager.refactor_suggestion(code, language)

async def get_contextual_answer(prompt: str, project_path: str = None) -> str:
    return await chat_manager.get_contextual_answer(prompt, project_path)

def get_conversation_stats() -> Dict:
    return chat_manager.get_conversation_stats()
