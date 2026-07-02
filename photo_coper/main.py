import os
import sys
import time
from pathlib import Path
from photo_coper import config, scanner, tui, copier

def main():
    print("Photo Coper v1.0")
    cfg = config.load_config()

    # Шаг 1: Сканирование и выбор групп
    files_by_date = None
    selected_dates = None

    while True:
        files_by_date = scanner.get_all_files(cfg['extensions'])
        selected_dates = tui.select_groups(files_by_date)

        if selected_dates == "refresh":
            continue
        if selected_dates:
            break
        else:
            print("Ничего не выбрано.")
            if not tui.questionary.confirm("Выход?").ask():
                continue
            else:
                sys.exit(0)

    # Проверка коллизий в выбранных файлах
    selected_files = []
    for date in selected_dates:
        selected_files.extend(files_by_date[date])

    collisions = scanner.check_name_collisions(selected_files)
    if collisions:
        print(f"\nВНИМАНИЕ: Найдено {len(collisions)} пересечений имен файлов.")
        print("Например:", ", ".join(collisions[:5]))

    # Шаг 2: Выбор каталога и ввод имени
    base_dest = tui.select_destination(cfg['destination_directories'])
    folder_name = tui.ask_folder_name(selected_dates)

    target_path = Path(base_dest) / folder_name

    # Шаг 3: Проверка существования
    if not tui.confirm_overwrite(target_path):
        # В идеале тут надо вернуться назад, но для упрощения предложим начать заново или выйти
        print("Операция отменена пользователем.")
        return main()

    # Шаг 4: Конфликты имен
    conflict_mode = 'none'
    if collisions:
        conflict_mode = tui.ask_conflict_resolution()
        # Если несколько дат и выбрано 'date', это логично.
        # Если выбрано 'number', нам нужно сопоставить каждый файл с номером папки.
        if conflict_mode == 'number':
            # Группируем по источникам (диск + папка)
            sources = sorted(list(set(f['path'].parent for f in selected_files)))
            source_to_num = {src: i+1 for i, src in enumerate(sources)}
            for f in selected_files:
                f['subdir'] = str(source_to_num[f['path'].parent])
        elif conflict_mode == 'date':
            for f in selected_files:
                f['ctime_str'] = scanner.datetime.fromtimestamp(f['ctime']).strftime("%Y-%m-%d")

    # Шаг 5: Удаление
    delete_after = tui.ask_delete_after()

    # Шаг 6: LR
    create_lr, launch_lr = tui.ask_lr_options()

    # Шаг 7: Подтверждение
    summary = f"""
    Будет скопировано файлов: {len(selected_files)}
    Размер: {tui.format_size(sum(f['size'] for f in selected_files))}
    Из дат: {', '.join(selected_dates)}
    В папку: {target_path}
    Разрешение конфликтов: {conflict_mode}
    Удаление после: {'Да' if delete_after else 'Нет'}
    Создать LR: {'Да' if create_lr else 'Нет'}
    Запустить LR: {'Да' if launch_lr else 'Нет'}
    """

    if not tui.final_confirm(summary):
        print("Отменено.")
        return

    # ВЫПОЛНЕНИЕ
    start_time = time.time()
    src_target = target_path / "src"
    os.makedirs(src_target, exist_ok=True)

    cp = copier.FileCopier(conflict_mode=conflict_mode, delete_after=delete_after)

    copied_count = 0
    skipped_count = 0

    from tqdm import tqdm
    # Используем tqdm для прогресса, если доступен, или просто принт
    pbar = tqdm(selected_files, desc="Копирование", unit="файл")

    try:
        for f_info in pbar:
            res = cp.copy_file(f_info, src_target)
            if res == "copied":
                copied_count += 1
            elif res == "skipped":
                skipped_count += 1

            # Прогресс в таскбар (заглушка)
            cp.update_taskbar_progress(copied_count + skipped_count, len(selected_files))

    except Exception as e:
        print(f"\nКРИТИЧЕСКАЯ ОШИБКА: {e}")
        tui.questionary.press_any_key_to_continue("Нажмите любую клавишу для выхода...").ask()
        return

    # Удаление
    if delete_after:
        print("Удаление исходных файлов...")
        for f_info in selected_files:
            try:
                # Удаляем только если файл существует в приемнике и идентичен
                # В нашей логике copy_file это уже гарантирует если не было ошибки
                os.remove(f_info['path'])
            except Exception as e:
                print(f"Ошибка при удалении {f_info['path']}: {e}")

    # LR
    if create_lr:
        lr_dir = target_path / "LR"
        os.makedirs(lr_dir, exist_ok=True)
        if cfg['lr_template_path']:
            print("Копирование шаблона Lightroom...")
            copier.copy_structure(cfg['lr_template_path'], lr_dir)

    end_time = time.time()
    duration = end_time - start_time

    print(f"\nГотово!")
    print(f"Скопировано: {copied_count}, пропущено: {skipped_count}")
    print(f"Время выполнения: {duration:.2f} сек.")

    if launch_lr:
        print("Запуск Lightroom...")
        # Ищем .lrcat в папке LR
        lr_dir = target_path / "LR"
        lrcat_files = list(lr_dir.glob("*.lrcat"))
        if lrcat_files:
            os.startfile(str(lrcat_files[0])) if hasattr(os, 'startfile') else print(f"Запустите вручную: {lrcat_files[0]}")
        else:
            # Запуск просто экзешника
            os.system(f"start {cfg['lightroom_exe']}")

    tui.questionary.press_any_key_to_continue("Нажмите любую клавишу для завершения...").ask()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nПрервано пользователем.")
