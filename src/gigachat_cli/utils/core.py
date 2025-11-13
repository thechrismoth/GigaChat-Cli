import os
import asyncio
import aiofiles
import re
from typing import List, Dict, Optional, AsyncGenerator, Union, Any
from dataclasses import dataclass
from enum import Enum

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_gigachat.chat_models import GigaChat

from gigachat_cli.utils.config import Config

class GigaChatErrorType(Enum):
    AUTHENTICATION = "authentication_error"
    RATE_LIMIT = "rate_limit_error" 
    NETWORK = "network_error"
    API = "api_error"
    CONTENT_FILTER = "content_filter"

@dataclass
class StreamChunk:
    content: str
    is_final: bool = False
    error: Optional[str] = None

class GigaChatError(Exception):
    def __init__(self, message: str, error_type: GigaChatErrorType, original_error: Optional[Exception] = None):
        self.message = message
        self.error_type = error_type
        self.original_error = original_error
        super().__init__(self.message)

class GigaChatManager:
    _instance: Optional['GigaChatManager'] = None
    
    def __new__(cls) -> 'GigaChatManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if not hasattr(self, '_initialized') or not self._initialized:
            self.conversation_history: List[Union[HumanMessage, AIMessage, SystemMessage]] = []
            self.config = Config()
            self.project_context: Dict[str, Any] = {}
            self._file_cache: Dict[str, str] = {}
            self._file_index: Dict[str, str] = {}
            self._last_files_context: List[str] = []
            self._last_user_messages: List[str] = []
            self._initialized = True
    
    def _get_api_key(self) -> str:
        """Получаем API ключ из переменных окружения"""
        api_key = os.getenv("GIGACHAT_API_KEY")
        if not api_key:
            raise GigaChatError(
                "GIGACHAT_API_KEY не установен. Пожалуйста, установите переменную окружения.",
                GigaChatErrorType.AUTHENTICATION
            )
        return api_key
    
    def _get_giga_chat_instance(self) -> GigaChat:
        """Создаем экземпляр GigaChat с текущей выбранной моделью из конфига"""
        current_model = self.config.get_model()
        
        return GigaChat(
            credentials=self._get_api_key(),
            verify_ssl_certs=False,
            model=current_model,
            scope="GIGACHAT_API_PERS",
            temperature=0.1,
            max_tokens=4000,
            timeout=60
        )
    
    async def send_message_stream(self, prompt: str, system_prompt: Optional[str] = None) -> AsyncGenerator[StreamChunk, None]:
        """
        Потоковая отправка сообщения с немедленным началом
        """
        try:
            giga = self._get_giga_chat_instance()
            
            # Сохраняем сообщение пользователя для контекста
            self._last_user_messages.append(prompt)
            if len(self._last_user_messages) > 5:
                self._last_user_messages = self._last_user_messages[-5:]
            
            # Подготавливаем сообщения с полной историей диалога
            messages: List[Union[HumanMessage, AIMessage, SystemMessage]] = []
            
            # Добавляем системный промпт с контекстом
            enhanced_system_prompt = self._enhance_system_prompt(system_prompt)
            if enhanced_system_prompt:
                messages.append(SystemMessage(content=enhanced_system_prompt))
                
            # ДОБАВЛЯЕМ ВСЮ ИСТОРИЮ ДИАЛОГА
            messages.extend(self.conversation_history)
            
            # Добавляем текущий запрос
            messages.append(HumanMessage(content=prompt))
            
            # НЕМЕДЛЕННО возвращаем пустой чанк чтобы UI не зависал
            yield StreamChunk(content="", is_final=False)
            
            full_response = ""
            
            try:
                # Используем asyncio.to_thread для неблокирующего выполнения
                loop = asyncio.get_event_loop()
                
                def create_stream():
                    return giga.stream(messages)
                
                stream = await loop.run_in_executor(None, create_stream)
                
                # Обрабатываем потоковые чанки
                for chunk in stream:
                    if hasattr(chunk, 'content') and chunk.content:
                        chunk_content = chunk.content
                        full_response += chunk_content
                        yield StreamChunk(content=chunk_content)
                
                # Финальный чанк
                yield StreamChunk(content="", is_final=True)
                
                # Сохраняем в историю
                if full_response:
                    self.conversation_history.append(HumanMessage(content=prompt))
                    self.conversation_history.append(AIMessage(content=full_response))
                    
                    # Ограничиваем историю
                    if len(self.conversation_history) > 20:
                        self.conversation_history = self.conversation_history[-20:]
                        
            except Exception as e:
                await self._handle_stream_error(e)
                
        except GigaChatError:
            raise
        except Exception as e:
            print(f"Unexpected error in send_message_stream: {e}")
            yield StreamChunk(content="", is_final=True, error=f"Unexpected error: {str(e)}")
    
    def _enhance_system_prompt(self, system_prompt: Optional[str] = None) -> str:
        """Добавляем контекст предыдущих сообщений в системный промпт"""
        base_prompt = system_prompt or "Ты - полезный AI-ассистент для разработчиков."
        
        # Добавляем информацию о последних сообщениях пользователя
        if len(self._last_user_messages) > 1:
            # Берем предыдущие сообщения (кроме текущего)
            previous_messages = self._last_user_messages[:-1]
            context_info = f"Предыдущие запросы пользователя: {'; '.join(previous_messages[-3:])}"
            return f"{base_prompt} {context_info}. Учитывай этот контекст при ответе."
        
        return base_prompt

    async def _handle_stream_error(self, error: Exception):
        """Обрабатываем ошибки потока"""
        error_str = str(error).lower()
        
        if "authentication" in error_str or "credential" in error_str:
            raise GigaChatError(
                "Ошибка аутентификации. Проверьте GIGACHAT_API_KEY",
                GigaChatErrorType.AUTHENTICATION,
                error
            )
        elif "rate" in error_str or "limit" in error_str:
            raise GigaChatError(
                "Превышен лимит запросов. Попробуйте позже.",
                GigaChatErrorType.RATE_LIMIT,
                error
            )
        elif "timeout" in error_str or "connection" in error_str:
            raise GigaChatError(
                "Ошибка сети или таймаут соединения",
                GigaChatErrorType.NETWORK,
                error
            )
        else:
            raise GigaChatError(
                f"Ошибка API: {str(error)}",
                GigaChatErrorType.API,
                error
            )

    # Строим индекс всех файлов в проекте для быстрого поиска
    def _build_file_index(self, project_path: Optional[str] = None) -> Dict[str, str]:
        if not project_path:
            project_path = os.getcwd()
        
        file_index: Dict[str, str] = {}
        
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
    def _find_file_in_project(self, filename: str, project_path: Optional[str] = None) -> Optional[str]:
        if not project_path:
            project_path = os.getcwd()
        
        # Если индекс еще не построен - строим
        if not self._file_index:
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
        except Exception:
            pass
        
        return None
   
    # Загружаем контекст проекта
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
    
    #Загружаем содержимое нескольких файлов по их именам
    async def load_multiple_files(self, file_names: List[str], project_path: Optional[str] = None) -> Dict[str, str]:
        files_content: Dict[str, str] = {}
        
        for file_name in file_names:
            # Находим полный путь к файлу в проекте
            full_path = self._find_file_in_project(file_name, project_path)
            
            if full_path and os.path.exists(full_path):
                content = await self.load_file_content(full_path)
                relative_path = os.path.relpath(full_path, project_path or os.getcwd())
                files_content[relative_path] = content or "[Пустой файл или ошибка чтения]"
                # Сохраняем в контекст последних файлов
                if relative_path not in self._last_files_context:
                    self._last_files_context.append(relative_path)
                    if len(self._last_files_context) > 10:
                        self._last_files_context = self._last_files_context[-10:]
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
    async def get_contextual_answer(self, prompt: str, project_path: Optional[str] = None) -> str:
        """Синхронная версия для обратной совместимости"""
        full_response = ""
        
        async for chunk in self.get_contextual_answer_stream(prompt, project_path):
            if chunk.content:
                full_response += chunk.content
            if chunk.error:
                raise GigaChatError(chunk.error, GigaChatErrorType.API)
        
        return full_response
    
    async def get_contextual_answer_stream(self, prompt: str, project_path: Optional[str] = None) -> AsyncGenerator[StreamChunk, None]:
        """Потоковая версия с контекстом файлов"""
        if not project_path:
            project_path = os.getcwd()
        
        # Ищем упоминания файлов в запросе
        referenced_files = self._extract_file_references(prompt)
        
        # УМНОЕ ОПРЕДЕЛЕНИЕ "ЭТОГО ФАЙЛА" - смотрим в последних сообщениях пользователя
        if any(phrase in prompt.lower() for phrase in ['этот файл', 'тот файл', 'предыдущий файл', 'the file']):
            # Ищем упоминания файлов в предыдущих сообщениях пользователя
            for user_msg in reversed(self._last_user_messages[:-1]):  # Исключаем текущее сообщение
                files_in_history = self._extract_file_references(user_msg)
                if files_in_history:
                    referenced_files.extend(files_in_history)
                    print(f"Найдены файлы в истории пользователя: {files_in_history}")
                    break
        
        system_message = "Ты - опытный разработчик. Тебе предоставлено содержимое файлов проекта."
        
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
                
                async for chunk in self.send_message_stream(full_prompt, system_message):
                    yield chunk
                return
        
        # Если файлы не найдены, используем стандартный запрос с полной историей
        async for chunk in self.send_message_stream(prompt, system_message):
            yield chunk
    
    # Загружаем контекст проекта
    async def load_project_context(self, project_path: Optional[str] = None) -> Dict[str, Any]:
        if not project_path:
            project_path = os.getcwd()
        
        context: Dict[str, Any] = {
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
                        except Exception:
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
    async def get_code_analysis(self, prompt: str, project_path: Optional[str] = None) -> str:
        """Синхронная версия для обратной совместимости"""
        full_response = ""
        
        async for chunk in self.get_code_analysis_stream(prompt, project_path):
            if chunk.content:
                full_response += chunk.content
            if chunk.error:
                raise GigaChatError(chunk.error, GigaChatErrorType.API)
        
        return full_response
    
    async def get_code_analysis_stream(self, prompt: str, project_path: Optional[str] = None) -> AsyncGenerator[StreamChunk, None]:
        """Потоковая версия анализа кода"""
        context = await self.load_project_context(project_path)
        
        system_message = """Ты - опытный разработчик-ассистент. Анализируй код проекта и давай конкретные, 
        практические советы. Фокусируйся на:
        1. Качестве кода и лучших практиках
        2. Возможных ошибках и уязвимостях
        3. Оптимизации производительности
        4. Архитектурных улучшениях
        
        Будь конкретен и приводи примеры исправлений."""
        
        file_structure = context.get("file_structure", [])
        key_files = context.get("key_files", {})
        
        context_info = f"Структура проекта ({len(file_structure)} файлов):\n"
        context_info += "\n".join(file_structure[:25])
        
        if len(file_structure) > 25:
            context_info += f"\n... и еще {len(file_structure) - 25} файлов"
        
        context_info += "\n\n"
        
        if key_files:
            context_info += "Ключевые файлы:\n"
            key_files_items = list(key_files.items())[:5]
            for file, content in key_files_items:
                context_info += f"\n--- {file} ---\n{content[:1000]}\n"
        
        full_prompt = f"{context_info}\n\nЗапрос: {prompt}"
        
        async for chunk in self.send_message_stream(full_prompt, system_message):
            yield chunk
    
    # Основной метод для получания ответа
    async def get_answer(self, prompt: str, clear_history: bool = False) -> str:
        """Синхронная версия для обратной совместимости"""
        if clear_history:
            self.conversation_history.clear()
            return "История диалога очищена"
        
        full_response = ""
        
        async for chunk in self.get_answer_stream(prompt, clear_history):
            if chunk.content:
                full_response += chunk.content
            if chunk.error:
                raise GigaChatError(chunk.error, GigaChatErrorType.API)
        
        return full_response
    
    async def get_answer_stream(self, prompt: str, clear_history: bool = False) -> AsyncGenerator[StreamChunk, None]:
        """Потоковая версия основного метода"""
        if clear_history:
            self.conversation_history.clear()
            self._last_files_context.clear()
            self._last_user_messages.clear()
            yield StreamChunk(content="История диалога очищена", is_final=True)
            return
        
        # Автоматически определяем тип запроса
        if any(keyword in prompt.lower() for keyword in ['анализ', 'проект', 'project', 'структур']):
            async for chunk in self.get_code_analysis_stream(prompt):
                yield chunk
            return
        
        elif any(keyword in prompt.lower() for keyword in ['объясни', 'explain', 'как работает']):
            code_blocks = self._extract_code_blocks(prompt)
            if code_blocks:
                async for chunk in self.explain_code_stream(code_blocks[0], self._detect_language(prompt)):
                    yield chunk
                return
        
        elif any(keyword in prompt.lower() for keyword in ['рефакторинг', 'refactor', 'улучши код']):
            code_blocks = self._extract_code_blocks(prompt)
            if code_blocks:
                async for chunk in self.refactor_suggestion_stream(code_blocks[0], self._detect_language(prompt)):
                    yield chunk
                return
        
        # Для запросов с упоминанием файлов используем контекстный ответ
        elif (self._extract_file_references(prompt) or 
              any(keyword in prompt.lower() for keyword in ['файл', 'file', 'этот файл', 'тот файл'])):
            async for chunk in self.get_contextual_answer_stream(prompt):
                yield chunk
            return
        
        # Стандартный запрос с полной историей диалога
        system_message = "Ты - полезный AI-ассистент для разработчиков."
        async for chunk in self.send_message_stream(prompt, system_message):
            yield chunk

    # Потоковые версии специализированных методов
    async def explain_code_stream(self, code: str, language: str = "python") -> AsyncGenerator[StreamChunk, None]:
        system_message = f"""Ты - преподаватель программирования. Объясни этот {language} код простым языком:
        1. Что делает этот код?
        2. Как он работает пошагово?
        3. Какие ключевые конструкции используются?
        4. Есть ли потенциальные проблемы?"""
        
        full_prompt = f"Код для объяснения:\n```{language}\n{code}\n```"
        
        async for chunk in self.send_message_stream(full_prompt, system_message):
            yield chunk
    
    async def refactor_suggestion_stream(self, code: str, language: str = "python") -> AsyncGenerator[StreamChunk, None]:
        system_message = f"""Ты - senior разработчик. Проанализируй этот {language} код и предложи улучшения:
        1. Улучшение читаемости
        2. Оптимизация производительности  
        3. Следование best practices
        4. Устранение code smells
        
        Покажи конкретные примеры до/после."""
        
        full_prompt = f"Код для рефакторинга:\n```{language}\n{code}\n```"
        
        async for chunk in self.send_message_stream(full_prompt, system_message):
            yield chunk

    # Извлекаем блоки кода из текста
    def _extract_code_blocks(self, text: str) -> List[str]:
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
        self._last_files_context.clear()
        self._last_user_messages.clear()
        return "История диалога очищена"
    
    def get_current_model(self) -> str:
        return self.config.get_model()
    
    def get_conversation_stats(self) -> Dict[str, Union[int, str, List[str]]]:
        """Статистика текущей сессии"""
        user_messages = sum(1 for msg in self.conversation_history if isinstance(msg, HumanMessage))
        ai_messages = sum(1 for msg in self.conversation_history if isinstance(msg, AIMessage))
        
        return {
            "total_messages": len(self.conversation_history),
            "user_messages": user_messages,
            "ai_messages": ai_messages,
            "current_model": self.get_current_model(),
            "last_files_context": self._last_files_context
        }

# Создаем инстанс
chat_manager = GigaChatManager()

# Функции для обратной совместимости
async def get_answer(prompt: str, clear_history: bool = False) -> str:
    return await chat_manager.get_answer(prompt, clear_history)

async def get_answer_stream(prompt: str, clear_history: bool = False) -> AsyncGenerator[StreamChunk, None]:
    """Потоковая версия"""
    async for chunk in chat_manager.get_answer_stream(prompt, clear_history):
        yield chunk

# Очистка истории
def clear_chat_history() -> str:
    return chat_manager.clear_history()

# Получение текущей модели
def get_current_model() -> str:
    return chat_manager.get_current_model()

# Новые функции для работы с кодом
async def analyze_project(prompt: str, project_path: Optional[str] = None) -> str:
    return await chat_manager.get_code_analysis(prompt, project_path)

async def analyze_project_stream(prompt: str, project_path: Optional[str] = None) -> AsyncGenerator[StreamChunk, None]:
    """Потоковая версия анализа проекта"""
    async for chunk in chat_manager.get_code_analysis_stream(prompt, project_path):
        yield chunk

async def explain_code(code: str, language: str = "python") -> str:
    full_response = ""
    async for chunk in chat_manager.explain_code_stream(code, language):
        if chunk.content:
            full_response += chunk.content
        if chunk.error:
            raise GigaChatError(chunk.error, GigaChatErrorType.API)
    return full_response

async def explain_code_stream(code: str, language: str = "python") -> AsyncGenerator[StreamChunk, None]:
    """Потоковая версия объяснения кода"""
    async for chunk in chat_manager.explain_code_stream(code, language):
        yield chunk

async def refactor_code(code: str, language: str = "python") -> str:
    full_response = ""
    async for chunk in chat_manager.refactor_suggestion_stream(code, language):
        if chunk.content:
            full_response += chunk.content
        if chunk.error:
            raise GigaChatError(chunk.error, GigaChatErrorType.API)
    return full_response

async def refactor_code_stream(code: str, language: str = "python") -> AsyncGenerator[StreamChunk, None]:
    """Потоковая версия рефакторинга"""
    async for chunk in chat_manager.refactor_suggestion_stream(code, language):
        yield chunk

async def get_contextual_answer(prompt: str, project_path: Optional[str] = None) -> str:
    return await chat_manager.get_contextual_answer(prompt, project_path)

async def get_contextual_answer_stream(prompt: str, project_path: Optional[str] = None) -> AsyncGenerator[StreamChunk, None]:
    """Потоковая версия контекстного ответа"""
    async for chunk in chat_manager.get_contextual_answer_stream(prompt, project_path):
        yield chunk

def get_conversation_stats() -> Dict[str, Union[int, str, List[str]]]:
    return chat_manager.get_conversation_stats()
