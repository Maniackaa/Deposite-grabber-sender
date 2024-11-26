import os
import time
from pathlib import Path

from adbutils import AdbClient

from config_data.conf import get_my_loggers, conf

logger, *other = get_my_loggers()

BASE_DIR = Path(__file__).resolve().parent

SCREEN_FOLDER = Path(conf.adb.SCREEN_FOLDER)
TARGET_DIR = BASE_DIR / 'screenshots'


def get_file_list(directory, adb_device):
    """
    Получение списка файлов из директории с их размерами
    """
    command = f'ls -l {directory}'
    files_output = adb_device.shell(command)
    files = files_output.splitlines()
    file_list = []
    for file in files:
        if file.startswith('total'):
            continue
        items = file.split()
        if len(items) >= 5:
            file_name = items[-1]
            file_size = int(items[4])
            file_list.append((file_name, file_size))
    return file_list


def main():
    small_file_count = 0
    while True:
        # adb_client = AdbClient(host="host.docker.internal", port=5037)
        # adb_client = AdbClient(host="127.0.0.1", port=5037)
        adb_client = AdbClient(host=os.getenv('HOST'), port=5037)
        adb_devices = adb_client.device_list()
        if adb_devices:
            adb_device = adb_devices[0]
            device_name = adb_device.info.get('serialno')
            logger.info(f'Подключено: {device_name}')
        else:
            time.sleep(5)
            continue
        try:
            data = get_file_list(SCREEN_FOLDER.as_posix(), adb_device)
            logger.debug(f'Количество скринов: {len(data)}')
            logger.debug(str(data))
            if data:
                file, size = data[0][0], data[0][1]
                file_path = SCREEN_FOLDER / file
                if size > 150000:
                    small_file_count = 0
                    logger.debug(f'Скачиваем файл {file} {size} кб')
                    file_name = file.replace('.jpg', f'_from_{device_name}.jpg')
                    # target_path_copy = TARGET_DIR / 'Copy' / file_name
                    # downloaded_copy = adb_device.sync.pull(file_path.as_posix(), target_path_copy.as_posix())
                    target_path = TARGET_DIR / file_name
                    downloaded = adb_device.sync.pull(file_path.as_posix(), target_path.as_posix())
                    if downloaded:
                        logger.debug(f'Удаляем файл {file}: {downloaded}')
                        adb_device.shell(f'rm {file_path.as_posix()}')
                else:
                    # Если маленький файл
                    logger.debug(f'маленький файл {file_path}')
                    if small_file_count > 3:
                        adb_device.shell(f'rm {file_path.as_posix()}')
                        logger.debug('Удален маленький файл')
                        small_file_count = 0
                    else:
                        small_file_count += 1
                        logger.debug(f'small_file_count: {small_file_count}')
            else:
                time.sleep(3)
            time.sleep(0.5)
        except Exception as err:
            logger.debug(err, exc_info=True)
            time.sleep(5)


if __name__ == '__main__':
    main()
