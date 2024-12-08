import time

import requests
from urllib3.exceptions import NewConnectionError

from config_data.conf import get_my_loggers
from config_data.conf import BASE_DIR, conf

path = BASE_DIR / 'screenshots'

logger, err_log, *other = get_my_loggers()

ENDPOINT = conf.adb.ENDPOINT
WORKER = conf.adb.WORKER


def save_copy(binary, name):
    try:
        file_path = path / 'Copy2' / name
        with open(file_path, 'wb+') as file:
            file.write(binary)
    except Exception as err:
        logger.error(err)


def main():
    while True:
        try:
            global_start = time.perf_counter()
            files = list(path.glob('*.jpg'))
            time.sleep(1)
            logger.debug(f'{files}')
            for file in files:
                try:
                    start = time.perf_counter()
                    size = file.lstat().st_size
                    if size > 300000:
                        logger.debug(f'Удаляем большой файл {file.name}')
                        file.unlink()
                        pass

                    elif size > 0:
                        file_name = file.name
                        logger.debug(f'Отправляем {file_name, size, bool(size>0)}')
                        # with open(file, "rb") as binary:
                        #     readed_file = binary.read()
                        #     save_copy(readed_file, file_name)
                        with open(file, "rb") as binary:
                            screen = {'image': binary}
                            response = requests.post(ENDPOINT, data={'name': file_name, 'worker': WORKER}, files=screen, timeout=10)
                            reason = response.reason
                            logger.debug(f'reason: {reason}')
                            logger.debug(f'{response, response.status_code}')
                            logger.debug(f'Время отправки: {time.perf_counter() - start}')

                        if response.status_code in [200, 201]:
                            file.unlink()
                            logger.debug(f'Скрин удален')
                        elif response.status_code in [502]:
                            time.sleep(5)
                except NewConnectionError:
                    time.sleep(5)
                except Exception as err:
                    logger.error(f'Ошибка обработки файла {file.name}: {err}')
                    err_log.error(err, exc_info=True)
                    time.sleep(0.1)

            logger.debug(f'Общее время: {time.perf_counter() - global_start}')
            logger.debug('----')

        except Exception as err:
            time.sleep(5)
            logger.eror(err)
            err_log.error(err, exc_info=True)


if __name__ == '__main__':
    main()
