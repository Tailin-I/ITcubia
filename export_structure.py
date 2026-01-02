import os

def export_python_code_to_txt(project_root_dir, output_file_name="project_code.txt"):
    """
    выгружает весь код в 1 .txt чтобы потешить самолюбие и посмотреть сколько строчек кода уже написано)

    Args:
        project_root_dir (str): Абсолютный или относительный путь к корневой директории проекта.
        output_file_name (str): Имя файла, в который будет записан код.
    """
    project_root_dir = os.path.abspath(project_root_dir)
    output_path = os.path.join(os.getcwd(), output_file_name) # Сохраняем в текущей директории запуска скрипта

    excluded_dirs = ['.venv', '__pycache__', '.git', 'build', 'dist', 'node_modules', 'logs']

    with open(output_path, 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk(project_root_dir):
            # Изменяем dirs на месте, чтобы os.walk() не заходил в исключенные директории
            dirs[:] = [d for d in dirs if d not in excluded_dirs]

            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    # Получаем относительный путь от корня проекта
                    relative_path = os.path.relpath(full_path, project_root_dir)

                    outfile.write(f"### Файл: {relative_path}\n")
                    outfile.write(f"### Полный путь: {full_path}\n")
                    outfile.write("-" * 80 + "\n") # Разделитель для читаемости

                    try:
                        with open(full_path, 'r', encoding='utf-8') as infile:
                            code_content = infile.read()
                            outfile.write(code_content)
                        outfile.write("\n" + "=" * 80 + "\n\n") # Еще один разделитель
                        print(f"  Добавлен файл: {relative_path}")
                    except UnicodeDecodeError:
                        outfile.write(f"!!! Ошибка чтения файла (неверная кодировка): {relative_path}\n")
                        print(f"  Пропущено (ошибка кодировки): {relative_path}")
                    except Exception as e:
                        outfile.write(f"!!! Ошибка при чтении файла {relative_path}: {e}\n")
                        print(f"  Пропущено (ошибка): {relative_path}")

    print(f"файл: {output_path}\n")

if __name__ == "__main__":
    export_python_code_to_txt(".", "project_code.txt")