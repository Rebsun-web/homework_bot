import logging
import os
import requests
from dotenv import load_dotenv
import time
import telegram
import sys
from http import HTTPStatus

# from telegram.ext import CommandHandler, Updater
# from telegram.ext import Filters, MessageHandler
# from telegram import ReplyKeyboardMarkup

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


class TokensValueException(Exception):
    """Класс проверки токенов на сущестование."""

    pass


class RequestStatusExeption(Exception):
    """Класс проверки статуса респонса."""

    pass


class NoStatusOrUndocumenated(Exception):
    """Класс проверки статуса респонса."""

    pass


class NoKeyHomeworksInResponse(Exception):
    """Класс проверки наличия ключа в словаре респонса."""

    pass


class HwStatusDidNotChange(Exception):
    """Класс проверки наличия ключа в словаре респонса."""

    pass


class HwHasNotBeenSent(Exception):
    """Класс проверки наличия ключа в словаре респонса."""

    pass


def check_tokens():
    """Проверяет доступность переменных окружения."""
    fl = True
    if PRACTICUM_TOKEN is None:
        fl = False
    elif PRACTICUM_TOKEN is None:
        fl = False
    elif TELEGRAM_CHAT_ID is None:
        fl = False
    return fl


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except telegram.error.TelegramError as error:
        logger.error('Сообщение не отправлено из-за ошибки: {error}')
        raise error('Сообщение не отправлено из-за ошибки: {error}')
    else:
        logger.debug('Успешная отправка сообщения в Telegram')


def get_api_answer(timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
    except Exception as RequestException:
        logger.error(f'Ошибка при запросе к основному API: {RequestException}')
    if homework_statuses.status_code != HTTPStatus.OK:
        logger.error(
            f'Статус ответа с эндрпоитна: {homework_statuses.status_code}'
        )
        raise RequestStatusExeption(
            f'Статус ответа с эндрпоитна: {homework_statuses.status_code}'
        )
        # response = homework_statuses.json()
    response = homework_statuses.json()
    return response


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if type(response) != dict:
        logger.error('В ответе API структура данных'
                     'не является словарем')
        raise TypeError('В ответе API структура данных'
                        'не является словарем')
    if type(response.get('homeworks')) != list:
        logger.error('В ответе API домашки под ключом `homeworks` '
                     'данные приходят не в виде списка.')
        raise TypeError('В ответе API домашки под ключом `homeworks` '
                        'данные приходят не в виде списка.')
    if 'homeworks' not in response:
        logger.error('В ответе API домашки'
                     'нет ключа `homeworks`')
        raise KeyError('В ответе API домашки'
                       'нет ключа `homeworks`')
    return response.get('homeworks')


def parse_status(homework):
    """Извлекает статус домашней работы."""
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    verdict = HOMEWORK_VERDICTS.get(status)
    if homework['status'] not in HOMEWORK_VERDICTS:
        logger.error('Неизвестный статус дз')
        raise NoStatusOrUndocumenated('Неизвестный статус дз')
    elif 'homework_name' not in homework:
        raise NoStatusOrUndocumenated('В дз нет ключа homework_name')
    elif 'status' not in homework:
        raise NoStatusOrUndocumenated('В дз нет ключа status')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    timestamp = int(time.time())
    status = ''
    if check_tokens():
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        while True:
            try:
                response = get_api_answer(timestamp)
                if check_response(response) is not None:
                    logger.debug('Проверка API прошла успешно')
                    homeworks = check_response(response)
                    timestamp = response.get('current date', timestamp)
                    if len(homeworks) > 0:
                        homework = homeworks[0]
                        new_status = homework.get('status')
                        if new_status != status:
                            status = new_status
                            message = parse_status(homework)
                            send_message(bot, message)
                            logger.debug(
                                'Успешная отправка сообщения в Telegram'
                            )
                        else:
                            logger.debug('Статус работы не изменился')
                            raise HwStatusDidNotChange(
                                'Статус работы не изменился'
                            )
                    else:
                        logger.info('Работа еще не отправдена на проверку')
                        raise HwHasNotBeenSent(
                            'Работа еще не отправдена на проверку'
                        )
                else:
                    logger.error('Проверка API не пройдена')
            except Exception as error:
                logger.error(f'Сбой в работе программы: {error}')
                message = f'Сбой в работе программы: {error}'
                send_message(bot, message)
            finally:
                time.sleep(RETRY_PERIOD)
    else:
        logger.critical('Отсутствие обязательных переменных '
                        'окружения')
        sys.exit()


if __name__ == '__main__':
    main()
