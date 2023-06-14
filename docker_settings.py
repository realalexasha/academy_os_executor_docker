import os

NUMBER = int(os.getenv('NUMBER', 5))
FIRST_PORT = int(os.getenv('PORT_FIRST', 5050))
NUMBER_OF_ATTEMPTS = int(os.getenv('NUMBER', 10))

GRAYLOG_HOST = os.getenv('GRAYLOG_HOST')
GRAYLOG_PORT = os.getenv('GRAYLOG_PORT')
GRAYLOG_SOURCE = os.getenv('GRAYLOG_SOURCE')
