# GigaChat CLI

[![PyPI Version](https://img.shields.io/pypi/v/gigachat-cli.svg)](https://pypi.org/project/gigachat-cli/)
[![PyPI - License](https://img.shields.io/pypi/l/gigachat-cli)](https://gitverse.ru/THEChrismoth/GigaChat-Cli/content/master/LICENSE.md)
[![Python Version](https://img.shields.io/pypi/pyversions/gigachat-cli)](https://pypi.org/project/gigachat-cli/)

Текстовый интерфейс для работы с GigaChat AI через командную строку с поддержкой терминальных команд и работы с файлами.

![GigaChat CLI Screenshot](https://gitverse.ru/api/repos/THEChrismoth/GigaChat-Cli/raw/branch/asset/gigachat_menu.jpg)

## Особенности

- **Интуитивный текстовый интерфейс** - современный TUI на базе Textual
- **Интерактивный чат** - общайтесь с GigaChat в реальном времени
- **Встроенный терминал** - выполняйте системные команды прямо из чата (префикс ёёё!ёёё)
- **Работа с файлами** - загружайте и анализируйте файлы с помощью команды ёёё/fileёёё
- **История диалога** - автоматическое сохранение контекста беседы
- **Подсветка синтаксиса** - красивый вывод кода и терминальных команд

## Установка

### Установка из PyPI
```
pip install gigachat-cli
```
### Установка из исходного кода
```
git clone https://gitverse.ru/THEChrismoth/GigaChat_Cli.git
cd gigachat_cli
pip install .
```
## Настройка аутентификации

### Получение API ключа

1. Перейдите на [SberAI Developer Studio](https://developers.sber.ru/studio/login)
2. Зарегистрируйтесь или войдите в аккаунт
3. Создайте новый API ключ

### Настройка переменной окружения
```
export GIGACHAT_API_KEY="ваш_api_ключ_здесь"
```
Для постоянного хранения добавьте в ваш ~/.bashrc, ~/.zshrc или ~/.profile:
```
echo 'export GIGACHAT_API_KEY="ваш_api_ключ_здесь"' >> ~/.bashrc
```
## Начало работы

### Запуск приложения
```
gigachat
```
### Основное использование

1. **Запустите приложение** - введите команду gigachat
2. **Выберите "Начать чат"** - из главного меню
3. **Введите сообщение** - пишите вопросы и нажимайте Shift+Enter для отправки
4. **Используйте терминальные команды** - начинайте команды с ёёё!ёёё (например: ёёё!ls -laёёё)
5. **Работайте с файлами** - используйте ёёё/file имя_файла ваш_запросёёё
6. **Выход** - введите ёёё/exitёёё или нажмите Ctrl+Q

![GigaChat CLI Screenshot](https://gitverse.ru/api/repos/THEChrismoth/GigaChat-Cli/raw/branch/asset/gigachat_work.jpg)

## Горячие клавиши

- **Shift+Enter** - отправить сообщение
- **Ctrl+Shift+V** - вставить текст из буфера обмена
- **Ctrl+Q** - выйти из приложения
- **Escape** - вернуться назад (в меню помощи)

## Примеры использования

### Базовый чат

Просто введите ваш вопрос и нажмите Shift+Enter

### Терминальные команды

- `!pwd` - показать текущую директорию
- `!python --version` - проверить версию Python  
- `!git status` - проверить статус git репозитория

### Работа с файлами

- `/file main.py объясни что делает этот код` - анализ кода Python
- `/file README.md улучши этот README файл` - улучшение документации
- `/file data.json проанализируй эту JSON структуру` - анализ JSON данных

## Требования

- Python >= 3.13
- GigaChat API ключ

## Зависимости

- textual >= 6.2.0 - фреймворк для TUI приложений
- langchain-gigachat >= 0.3.12 - интеграция с GigaChat
- asyncio >= 4.0.0 - асинхронное программирование

## Лицензия

MIT License - смотрите файл [LICENSE.md](LICENSE.md) для деталей.

## Поддержка

Если вы столкнулись с проблемами или у вас есть предложения:

1. Создайте issue в репозитории
2. Убедитесь что GIGACHAT_API_KEY корректно установлен
3. Проверьте что Python версии 3.13 или выше

---

**GigaChat CLI** - мощный инструмент для разработчиков, сочетающий возможности AI-ассистента с удобством командной строки.