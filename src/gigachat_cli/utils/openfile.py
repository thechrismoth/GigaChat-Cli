def open_file(file_name: str) -> str:
    """
    Открытие и чтение содержимого файла
    
    Args:
        file_name: Имя файла для чтения
        
    Returns:
        str: Содержимое файла или сообщение об ошибке
    """
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            file_content = f.read()
        return file_content
    except (IOError, UnicodeDecodeError) as e:
        return f"Ошибка чтения файла: {e}"
