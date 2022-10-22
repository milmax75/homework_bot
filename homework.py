from exceptions import (
    APIUnavailableException,
    APINotRespondedException,
    HomeworkDataError,
    HomeworkStatusError
)
from http import HTTPStatus
from logging import StreamHandler
from dotenv import load_dotenv

import logging
import os
import requests
import sys
import telegram
import time

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
HEADERS = {'Authorization': f"OAuth {PRACTICUM_TOKEN}"}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG)

handler = StreamHandler(stream=sys.stdout)
logging.getLogger('').addHandler(handler)


def send_message(bot, message):
    """Sends message from parse_status function to telegram bot chat."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        success_message = 'удачная отправка сообщения в Telegram'
        logging.info(success_message)
    except Exception as error:
        fail_message = f'Cбой при отправке сообщения в Telegram {error}'
        logging.error(fail_message)


def get_api_answer(current_timestamp):
    """Receives response from Yandex API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        logging.info('Request to API sent')
        if response.status_code != HTTPStatus.OK:
            raise APINotRespondedException('Responce not received')
        try:
            return response.json()
        except TypeError:
            logging.error('Not json format received')
    except Exception as error:
        print(error)
        raise APIUnavailableException(f'API not available')


def check_response(response):
    """Checking if response bears valid information."""
    if not isinstance(response, dict):
        logging.error('Info received is not a dictionary')
        raise TypeError('Info received is not a dictionary')

    if 'homeworks' not in response:
        logging.error('No new status received')
        raise KeyError('No new status received')
    homeworks = response.get('homeworks')
    homework = homeworks[0]
    try:
        return homework
    except IndexError:
        logging.error('Empty list received')


def parse_status(homework):
    """Gets status of the homework from the information received."""
    if 'homework_name' not in homework:
        logging.error('No homework info')
        raise KeyError('No homework info')
    if not isinstance(homework, dict):
        logging.error('Info received is not a dictionary')
        raise TypeError('Info received is not a dictionary')
    try:
        homework_name = homework.get('homework_name')
        homework_status = homework.get('status')
        if homework_status is None or homework_status not in HOMEWORK_STATUSES:
            logging.error('Unknown status')
            raise HomeworkStatusError('Unknown status')
    except Exception as error:
        HomeworkDataError(f'Data received cant be parsed {error}')
        logging.error(f'Data received cant be parsed {error}')
    else:
        verdict = HOMEWORK_STATUSES.get(homework_status)
        success_message = 'удачная отправка сообщения в Telegram'
        logging.info(success_message)
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    if not (PRACTICUM_TOKEN is None
            or TELEGRAM_TOKEN is None
            or TELEGRAM_CHAT_ID is None):
        return True


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    check_tokens()
    while True:
        try:
            response1 = get_api_answer(current_timestamp)
            homework1 = check_response(response1)
            time.sleep(RETRY_TIME)
            response2 = get_api_answer(current_timestamp)
            homework2 = check_response(response2)
            if homework2 != homework1:
                message = parse_status(homework2)
        except Exception as error:
            fail_message = f'Сбой в работе программы: {error}'
            logging.error(fail_message)
            time.sleep(RETRY_TIME)
        else:
            send_message(bot, message)
            logging.info('Message sent successfully')


if __name__ == '__main__':
    main()
