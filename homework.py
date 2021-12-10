import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

import exceptions

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log', filemode='w',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
)


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


def send_message(bot, message):
    """Функция отправки сообщения в Телеграм."""
    try:
        logging.debug(f'Отправка сообщения {message}в Телеграм')
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.info('Сообщение отправлено')
    except Exception as error:
        logging.error(f'Произошла ошибка при отправке сообщения {error}')


def get_api_answer(current_timestamp):
    """Функция выполняет запрос в АПИ Я.Практикум.
    При успешном запросе возвращает тело ответа в JSON
    """
    timestamp = current_timestamp
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != HTTPStatus.OK:
        logging.error(f'{ENDPOINT} вернул код ответа {response.status_code}')
        raise exceptions.NegativeValueException(f'URL {ENDPOINT} недоступен ')
    try:
        response = response.json()
    except ValueError:
        logging.error(f'В ответе от:{ENDPOINT} отсутсвует корректный JSON')
        raise ValueError(f'В ответе от:{ENDPOINT} отсутсвует корректный JSON')
    return response


def check_response(response):
    """Функция проверяет корректность тела ответа от АПИ Я.Практикум."""
    if isinstance(response, list) is True:
        response = response[0]
    elif 'homeworks' not in response:
        raise exceptions.NegativeValueException(
            'В ответе от Практикум.Домашки отсуствует homeworks')
    elif len(response['homeworks']) == 0:
        raise exceptions.NegativeValueException(
            'В ответе от Практикум.Домашки  пустой список')
    elif isinstance(response['homeworks'], list) is False:
        raise exceptions.NegativeValueException(
            'В ответе от Практикум.Домашки в homeworks нет списка'
            'либо работу ещё не взяли на ревью')
    elif isinstance(response['homeworks'][0], dict) is False:
        raise exceptions.NegativeValueException(
            'В ответе от Практикум.Домашки нет словаря'
        )
    return response['homeworks']


def parse_status(homework):
    """Фунция парсит тело ответа на переменные."""
    logging.info(f'Получена домашняя работа {homework}')
    if isinstance(homework, list) is True:
        homework = homework[0]
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    try:
        verdict = HOMEWORK_STATUSES[homework_status]
    except KeyError:
        logging.error('В ответе от Практикум.Домашки '
                      'неизвестынй статус домашки')
        raise KeyError(
            'В ответе от Практикум.Домашки '
            'неизвестынй статус работы'
        )
    if homework_name is None:
        raise exceptions.NegativeValueException('В ответе Практикум.Домашки '
                                                'отсутсвует имя домашки')
    logging.info(f'Изменился статус проверки работы "{homework_name}". '
                 f'{verdict}')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Функцию необходимо вызывать при запуске основной логики бота.
    Проверяет наличие переменных окружения.
    """
    env_vars = {
        PRACTICUM_TOKEN: 'PRACTICUM_TOKEN',
        TELEGRAM_TOKEN: 'TELEGRAM_TOKEN',
        TELEGRAM_CHAT_ID: 'TELEGRAM_CHAT_ID'
    }
    for var in env_vars.keys():
        var_name = env_vars[var]
        logging.debug(f'Проверка наличия переменной окружения: {var_name}')
        if var is None:
            logging.critical(f'Переменная окружения {var_name}')
            return False
        else:
            logging.info(f'Переменная окружения {var_name} присутствует')
    return True


def main():
    """Основная логика работы бота."""
    logging.debug('Запуск Telegram-бота')
    if check_tokens() is False:
        logging.critical(
            'Приложение остановлено, '
            'отсуствуют необходимые переменные окружения'
        )
        raise exceptions.NegativeValueException('Отсуствуют необходимые '
                                                'переменные окружения')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    last_message = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            if message != last_message:
                last_message = message
                send_message(bot, message)

            current_timestamp = int(time.time())
        except Exception as error:
            error_message = f'Сбой в работе программы: {error}'
            logging.error(error_message)
            if error_message != last_message:
                last_message = error_message
                # Если возник Exception при отправке сообщения об ошибке
                # то нужно его и тут перехватить
                try:
                    send_message(bot, error_message)
                except Exception:
                    ...
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
