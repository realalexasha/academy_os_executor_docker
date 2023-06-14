import logging
from graylog import CustomGELFTCPHandler as GELFTCPHandler
import docker_settings as settings
from graylog import get_graypy_logger

# отключаем логирования Flask
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# настраивем логирование
logger = get_graypy_logger()
logger.setLevel(logging.DEBUG)

logging.basicConfig(
    handlers=[
        GELFTCPHandler(
            host=settings.GRAYLOG_HOST,
            port=settings.GRAYLOG_PORT
        )
    ],
    format=(
        '{levelname} {asctime} {module} '
        '{process:d} {thread:d} {message}'
    ),
    style='{'
)