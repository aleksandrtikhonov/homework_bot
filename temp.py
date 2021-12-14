import os

from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


def check_tokens():
    """Провереряет доступность переменных окружения."""
    token_lst = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
    for token in token_lst:
        if token not in os.environ or os.environ.get(token) == '':
            return False
    return True


print('Результат - ', check_tokens())
