import logging
from graypy import GELFTCPHandler
import docker_settings as settings

OVERRIDE_KEY = 'graylog_override'


def get_graypy_logger(**extra):
    """Возвращает graylog логгер."""
    data = {OVERRIDE_KEY: {'host': settings.GRAYLOG_SOURCE}}

    data.update(extra)
    return GraylogLoggerAdapter(
        logging.getLogger(__name__),
        data
    )


class CustomGELFTCPHandler(GELFTCPHandler):
    """
    Кастомный обработчик TCP логирования в graylog.
    Добавлен функционал переопределения основных полей логов (по типу source).
    """

    def _make_gelf_dict(self, record):
        gelf_dict = super()._make_gelf_dict(record)
        self._override_graypy_data(record, gelf_dict)
        return gelf_dict

    @staticmethod
    def _override_graypy_data(record, gelf_dict: dict):
        data = getattr(record, OVERRIDE_KEY, {})
        if not data:
            return
        gelf_dict.update(data)
        if 'event_name' in data:
            # Если указано имя ивента, для удобства добавляем его в сообщение,
            # чтобы не приходилось заглядывать внутрь лога
            data['short_message'] = (
                f'[{data["event_name"]}]{data["short_message"]}'
            )
        # Сам словарь с переопределениями тоже запишется,
        # надо его убрать вручную
        unwanted_key = f'_{OVERRIDE_KEY}'
        gelf_dict.pop(unwanted_key)


class GraylogLoggerAdapter(logging.LoggerAdapter):

    def process(self, msg, kwargs):
        extra = kwargs.get('extra', {})
        # Объединяем параметры из адаптера, и переданные в логе
        extra.update(self.extra)
        kwargs['extra'] = extra
        return msg, kwargs