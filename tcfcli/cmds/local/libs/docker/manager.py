# -*- coding: utf-8 -*-

import docker
import click
import traceback
from tcfcli.common.operation_msg import  Operation

class ContainerManager(object):
    def __init__(self,
                 docker_network_id=None,
                 skip_pull_image=False,
                 is_quiet=False):

        self._docker_network_id = docker_network_id
        self._skip_pull_image = skip_pull_image
        self._docker_client = docker.from_env()

        self._is_quiet = is_quiet

    def run(self, container):
        image = container.image

        if not self.has_image(image) or not self._skip_pull_image:
            self.pull_image(image)
        else:
            if not self._is_quiet:
                Operation('skip pull image %s' % image).echo()

        if not container.is_exist():
            container.create()

        container.start()

    def stop(self, container):
        pass

    def pull_image(self, image):
        try:
            if not self._is_quiet:
                Operation('pull image %s...' % image, nl=False).echo()
            for _ in self._docker_client.api.pull(image, stream=True, decode=True):
                if not self._is_quiet:
                    Operation('.', nl=False).echo()
            if not self._is_quiet:
                Operation('\n').echo()
        except docker.errors.APIError as e:
            Operation(e, err_msg=traceback.format_exc(), level="ERROR").no_output()
            raise Exception('pull the docker image %s failed, %s' % (image, str(e)))

    def has_image(self, image):
        try:
            self._docker_client.images.get(image)
            return True
        except docker.errors.ImageNotFound as e:
            Operation(e, err_msg=traceback.format_exc(), level="ERROR").no_output()
            return False
