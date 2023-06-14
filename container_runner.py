import docker
import docker_settings as settings
from threading import Thread
import requests
import time
from log import logger
import json


class ContainerRunner:

    def __init__(self):
        self.containers = []

    def get_free_port(self):
        """
        :return: номер первого свободного порта из переменной настроек PORT.
        """
        busy_ports = []
        for item in self.containers:
            busy_ports.append(item['port'])
        current_port = settings.FIRST_PORT
        while True:
            if current_port not in busy_ports:
                return current_port
            current_port +=1

    def restart_container(self, container, port):
        """
        Останавливает работу конейнера и запускает новый на том же порте.

        :param container: объект <class 'docker.models.containers.Container'>.
        :param port: номер порта, на котором работает контейнер.
        """
        container.stop()
        logger.info(
            f"Stopped the container {container.short_id} on port {port}."
            )
        new_container = client.containers.run(
            "my-oscript", 
            detach=True, 
            ports={5000: port}
        )
        logger.info(
            f"Started the container {new_container.short_id} on port {port}."
        )
        self.containers.append({'container': new_container, 'port': port})

    

    def get_container(self):
        """
        Возвращает первый свободный контейнер.

        :return: объект <class 'docker.models.containers.Container'>.
        """
        while True:
            if len(self.containers) > 0:
                current_item = self.containers[0]
                self.containers.remove(current_item)
                logger.info(
                    "Got a container {current_item['container'].short_id} "
                    f"on port {current_item['port']}"
                )
                return current_item

            else:
                logger.warning(
                    f"Couldn't find a free container, "
                    "waiting for another attempt..."
                )
                time.sleep(1)

    def redirect_request(self, request):
        """
        Перенаправляет запрос в osweb_oscript_executor, запущенный в
        докер-контейнере и возвращет ответ, полученный от него, после чего 
        перезапускает докер-контейнер.

        :param request: объект <class 'werkzeug.local.LocalProxy'>.
        :return: объект <class 'requests.models.Response'>.
        """
        current_item = self.get_container()
        port = current_item['port']
        container = current_item['container']
        request_data = request.get_json()
        prescripts = request_data.get('prescript_code')
        if not prescripts:
            prescripts = ['']
        user_results = []
        reference_results = []
        for prescript in prescripts:
            request_data['prescript_code'] = prescript
            success = False
            for attempt_number in range(settings.NUMBER_OF_ATTEMPTS):
                try:
                    response = requests.get(
                        f"http://localhost:{port}/",
                        json=request_data
                    )
                    logger.info(
                        "Sent a request to container " 
                        f"{container.short_id} on port {port}."
                    )
                    success = True
                    break
                except:
                    logger.warning(
                        f"Couldn't send a request to container "
                        f"{container.short_id} on port {port}, "
                        "waiting for another attempt..."
                    )
                    # контейнер создался, но osweb_oscript_executor еще не успел 
                    # запуститься, поэтому ждём
                    time.sleep(1)
            if success:
                content = response.json()
                reference_result = content.get('reference_code', {})
                reference_results.append(reference_result)
                user_result = content.get('user_code', {})
                user_results.append(user_result)
            else:
                success = False
                break
        
        if success:
            # перезапускаем контейнер в фоне
            docker_thread = Thread(
                target=self.restart_container, args=[container, port]
            )
            docker_thread.start()

            content = {
                'reference_code': reference_results,
                'user_code': user_results
            }
            return json.dumps(content)
        logger.error("Couldn't find a free container.")
        return '{"server_error": "Couldn\'t find a free container."}'


logger.info("Ran the application")
runner = ContainerRunner()
client = docker.from_env()

# останавливаем все запущенные контейнеры
running_containers = client.containers.list()
for container in running_containers:
    tags = container.image.tags
    if len(tags) > 0 and tags[0] == 'my-oscript:latest':
        container.stop()
        logger.info(f"Stopped the old container {container.short_id}.")

# создаем докер образ
client.images.build(path="./app/", tag="my-oscript")

# создаем контейнеры в количестве, указанном в файле настроек
for index in range(settings.NUMBER):
    if len(runner.containers) < settings.NUMBER:
        port = runner.get_free_port()
        if port:
            try:
                container = client.containers.run(
                    "my-oscript", 
                    detach=True, 
                    ports={5000: port}
                )
                runner.containers.append(
                    {'container': container, 'port': port})
                logger.info(
                    f"Started container {container.short_id} on port {port}.")
            except:
                logger.error(f"Couldn't start a container on port {port}.")
                continue
