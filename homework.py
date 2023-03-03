import time
import sys

import requests
import os
from http import HTTPStatus

from dotenv import load_dotenv
import telegram
import logging
from exeptions import (RequestStatusExeption, NoStatusOrUndocumenated)


load_dotenv()


PRACTICUM_TOKEN = os.getenv('TOKEN_OF_PRAKTIKUM')
TELEGRAM_TOKEN = os.getenv('TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(message)s'
)

logger = logging.getLogger(__name__)


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all((PRACTICUM_TOKEN, PRACTICUM_TOKEN, TELEGRAM_CHAT_ID))


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        logger.info('Начало отправки сообщения в Telegram')
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except telegram.error.TelegramError as error:
        logger.error('Сообщение не отправлено из-за ошибки: {error}')
        raise error('Сообщение не отправлено из-за ошибки: {error}')
    else:
        logger.debug('Успешная отправка сообщения в Telegram')


def get_api_answer(timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    try:
        logger.info('Начало отправки запроса к API')
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
    except Exception as RequestException:
        logger.error(f'Ошибка при запросе к основному API: {RequestException}')
    if homework_statuses.status_code != HTTPStatus.OK:
        raise RequestStatusExeption(
            f'Статус ответа с эндрпоитна: {homework_statuses.status_code}'
        )
    return homework_statuses.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('В ответе API структура данных'
                        'не является словарем')
    if 'homeworks' not in response:
        raise KeyError('В ответе API домашки'
                       'нет ключа `homeworks`')
    if 'current_date' not in response:
        raise KeyError('В ответе API домашки'
                       'нет ключа `current_date`')
    if not isinstance(response.get('homeworks'), list):
        raise TypeError('В ответе API домашки под ключом `homeworks` '
                        'данные приходят не в виде списка.')
    return response.get('homeworks')


def parse_status(homework):
    """Извлекает статус домашней работы."""
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    verdict = HOMEWORK_VERDICTS.get(status)
    if homework['status'] not in HOMEWORK_VERDICTS:
        raise NoStatusOrUndocumenated('Неизвестный статус дз')
    if 'homework_name' not in homework:
        raise NoStatusOrUndocumenated('В дз нет ключа homework_name')
    if 'status' not in homework:
        raise NoStatusOrUndocumenated('В дз нет ключа status')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    timestamp = 0
    status = ''
    if not check_tokens():
        logger.critical('Отсутствие обязательных переменных '
                        'окружения')
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                logger.debug('Проверка API прошла успешно')
                timestamp = response.get('current date', timestamp)
                message = parse_status(homeworks[0])
                if message != status:
                    send_message(bot, message)
                    logger.debug(
                        'Успешная отправка сообщения в Telegram'
                    )
                    status = message
                else:
                    logger.debug('Статус работы не изменился')
            else:
                logger.debug(
                    'Нет отправленных домашних заданий'
                )
        except Exception as error:
            logger.error(f'Сбой в работе программы: {error}')
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
