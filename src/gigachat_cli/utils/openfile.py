def open_file(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        file_content = f.read()

    return file_content
