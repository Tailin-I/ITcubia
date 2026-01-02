import os
import sys


def generate_tree(directory, prefix="", ignore_dirs=None, ignore_files=None):
    """Генерирует древовидную структуру директории"""
    if ignore_dirs is None:
        ignore_dirs = {'.git', '__pycache__', '.idea', '.vscode'}
    if ignore_files is None:
        ignore_files = {'.pyc', '.pyo', '.pyd'}

    items = os.listdir(directory)
    items = [item for item in items if not item.startswith('.')]

    # Сначала директории, потом файлы
    dirs = sorted([item for item in items if os.path.isdir(os.path.join(directory, item))])
    files = sorted([item for item in items if not os.path.isdir(os.path.join(directory, item))])

    filtered_dirs = [d for d in dirs if d not in ignore_dirs]
    filtered_files = [f for f in files if not any(f.endswith(ext) for ext in ignore_files)]

    all_items = filtered_dirs + filtered_files

    for i, item in enumerate(all_items):
        is_last = i == len(all_items) - 1
        connector = "└── " if is_last else "├── "

        print(prefix + connector + item)

        path = os.path.join(directory, item)
        if os.path.isdir(path):
            extension = "    " if is_last else "│   "
            generate_tree(path, prefix + extension, ignore_dirs, ignore_files)


if __name__ == "__main__":
    start_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    print(os.path.basename(os.path.abspath(start_dir)) + "/")
    generate_tree(start_dir)