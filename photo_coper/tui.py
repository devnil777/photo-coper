import questionary
import sys
import os

def format_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

def select_groups(files_by_date):
    if not files_by_date:
        print("Изображения не найдены.")
        if not questionary.confirm("Обновить список?").ask():
            sys.exit(0)
        return None

    choices = []
    dates = sorted(files_by_date.keys())

    for date in dates:
        files = files_by_date[date]
        total_size = sum(f['size'] for f in files)
        count = len(files)
        drives = list(set(f['drive'] for f in files))
        exts = list(set(os.path.splitext(f['name'])[1].lower() for f in files))

        label = f"{date} ({format_size(total_size)}) {count} фото, Диски: {', '.join(drives)}, Типы: {', '.join(exts)}"
        choices.append(questionary.Choice(label, value=date))

    # Добавляем пункт Обновить
    choices.append(questionary.Separator())
    choices.append(questionary.Choice("Обновить список", value="refresh"))

    selected = questionary.checkbox(
        "Выберите группы для копирования:",
        choices=choices
    ).ask()

    if selected is None: # Ctrl+C
        sys.exit(0)

    if "refresh" in selected:
        return "refresh"

    return selected

def select_destination(dest_dirs):
    if not dest_dirs:
        # Если в конфиге нет папок, просим ввести
        path = questionary.path("Введите путь к каталогу назначения:").ask()
        if not path:
            sys.exit(0)
        return path

    choices = dest_dirs + ["Ввести другой путь..."]
    selected = questionary.select(
        "Выберите каталог куда копировать файлы:",
        choices=choices
    ).ask()

    if selected == "Ввести другой путь...":
        return questionary.path("Введите путь к каталогу назначения:").ask()

    return selected

def ask_folder_name(dates):
    if len(dates) == 1:
        name = questionary.text(f"Введите имя для папки (будет добавлено к {dates[0]}):").ask()
        return f"{dates[0]} {name}".strip()
    else:
        name = questionary.text("Введите имя всей папки целиком:").ask()
        return name

def confirm_overwrite(path):
    if os.path.exists(path) and os.listdir(path):
        return questionary.confirm(f"Папка {path} не пуста. Продолжить?").ask()
    return True

def ask_conflict_resolution():
    return questionary.select(
        "Как разрешить конфликты имен файлов?",
        choices=[
            questionary.Choice("Создать подпапки по датам (src/2023-01-01/...)", value="date"),
            questionary.Choice("Создать нумерованные подпапки (src/1/..., src/2/...)", value="number")
        ]
    ).ask()

def ask_delete_after():
    return questionary.confirm("Удалить исходные файлы после успешного копирования?").ask()

def ask_lr_options():
    create_lr = questionary.confirm("Создать каталог Lightroom?").ask()
    launch_lr = False
    if create_lr:
        launch_lr = questionary.confirm("Запустить Lightroom после завершения?").ask()
    return create_lr, launch_lr

def final_confirm(summary):
    print("\n--- План действий ---")
    print(summary)
    return questionary.confirm("Все верно? Начать копирование?").ask()
