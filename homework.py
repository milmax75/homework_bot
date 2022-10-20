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
    """Sends message from parse_status function to telegram bot chat. """
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        success_message = 'удачная отправка сообщения в Telegram'
        logging.info(success_message)
    except Exception as error:
        fail_message = f'Cбой при отправке сообщения в Telegram {error}'
        logging.error(fail_message)


def get_api_answer(current_timestamp):
    """Receives response from Yandex API. """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            raise APINotRespondedException('Responce not received'.format(
               ENDPOINT,
               HEADERS,
               params,
               response.status_code,
               response.reason,
               response.text
        ))
        return response.json()
    except Exception as error:
        raise APIUnavailableException('API not available'.format(
            ENDPOINT,
            HEADERS,
            params,
            error
        ))

def check_response(response):
    '''Checking if response bears valid information'''
    # response = get_api_answer()
    if not isinstance(response, dict):
        raise TypeError(
            logging.error('Info received is not a dictionary')
        )
    if isinstance(response, list):
        raise TypeError(
            logging.error('Info received is list')
        )
    if 'homeworks' not in response:
        raise KeyError(
            logging.error('No new status received')
        )
    homeworks = response.get('homeworks')
    homework = homeworks[0]
    return homework

def parse_status(homework):
    '''Gets status of the homework from the information received'''
    if 'homework_name' not in homework:
        raise KeyError(
            logging.error('No homework info')
        )
    if not isinstance(homework, dict):
        raise TypeError(
            logging.error('Info received is not a dictionary')
        )

    try:
        homework_name = homework.get('homework_name')
        homework_status = homework.get('status')
        if homework_status is None or homework_status not in HOMEWORK_STATUSES:
            raise HomeworkStatusError(
                logging.error('Unknown status')
            )
    except:
        HomeworkDataError(
            logging.error('Data received cant be parsed')
        )
    else:
        verdict = HOMEWORK_STATUSES.get(homework_status)
        success_message = 'удачная отправка сообщения в Telegram'
        logging.info(success_message)
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'

def check_tokens():
    '''Checking tokens validity'''
    tokens = {
        'PRACTICUM_TOKEN':PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN':TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID':TELEGRAM_CHAT_ID
    }
    for token in tokens.values():
        if token is None:
            return False
    return True

def main():
    """Основная логика работы бота."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    check_tokens()
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)
        except Exception as error:
            fail_message = f'Сбой в работе программы: {error}'
            logging.error(fail_message)
            time.sleep(RETRY_TIME)
        except:
            APINotRespondedException('Responce not received'.format(
            ENDPOINT,
            HEADERS,
            params,
            response.status_code,
            response.reason,
            response.text
        ))
        else:
            send_message(bot, message)

if __name__ == '__main__':
    main()
