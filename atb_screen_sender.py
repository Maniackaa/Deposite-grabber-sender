import json
import pickle
import time

import requests
from urllib3.exceptions import NewConnectionError

from config_data.conf import get_my_loggers
from config_data.conf import BASE_DIR, conf

path = BASE_DIR / 'atb_screenshots'

logger, err_log, *other = get_my_loggers()

ATB_ENDPOINT = conf.adb.ATB_ENDPOINT
OCR_ENDPOINT = conf.adb.OCR_ENDPOINT
WORKER = conf.adb.WORKER


def main():
    while True:
        try:
            global_start = time.perf_counter()
            files = list(path.glob('*.jpg'))
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
                        logger.debug(f'Отправляем {file.name, size, bool(size>0)}')
                        with open(file, "rb") as binary:
                            screen = {'image': binary}
                            response = requests.post(OCR_ENDPOINT, data={'name': file.name, 'worker': WORKER}, files=screen, timeout=10)
                            pay = response.reason
                            logger.debug(f'{response.status_code}')
                            logger.debug(f'pay: {pay}')
                            logger.debug(f'Время распознавания {time.perf_counter() - start}')
                        if response.status_code in [200]:
                            # Отправляем платеж

                            response = requests.post(ATB_ENDPOINT, data={'pay': pay, 'worker': WORKER, 'phone_name': phone_name }, timeout=10)
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
            time.sleep(0.5)

        except Exception as err:
            time.sleep(1)
            logger.eror(err)
            err_log.error(err, exc_info=True)


if __name__ == '__main__':
    main()
