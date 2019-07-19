"""Top-level package for codelab_adapter_client."""

__author__ = """Wenjie Wu"""
__email__ = 'wuwenjie718@gmail.com'
__version__ = '0.1.0'

import zmq
import time
import json
import logging
import sys
import threading
import msgpack
import queue
import psutil
from abc import ABCMeta, abstractmethod
from pathlib import Path
import importlib
import functools

ADAPTER_TOPIC = "from_adapter/extensions"
logger = logging.getLogger(__name__)


def threaded(function):
    """
    https://github.com/malwaredllc/byob/blob/master/byob/core/util.py#L514

    Decorator for making a function threaded
    `Required`
    :param function:    function/method to run in a thread
    """

    @functools.wraps(function)
    def _threaded(*args, **kwargs):
        t = threading.Thread(
            target=function, args=args, kwargs=kwargs, name=time.time())
        t.daemon = True  # 设置为daemon的线程会随着主线程的退出而结束
        t.start()
        return t

    return _threaded


class AdapterNode(metaclass=ABCMeta):
    '''
    CodeLab Adapter Node
    '''

    def __init__(
            self,
            name='',
            logger=logger,
            codelab_adapter_ip_address=None,
            subscriber_port='16103',
            publisher_port='16130',
            loop_time=0.1,
            connect_time=0.3,
            external_message_processor=None,
            receive_loop_idle_addition=None,
    ):
        '''
        :param codelab_adapter_ip_address: Adapter IP Address -
                                      default: 127.0.0.1
        :param subscriber_port: codelab_adapter subscriber port.
        :param publisher_port: codelab_adapter publisher port.
        :param loop_time: Receive loop sleep time.
        :param connect_time: Allow the node to connect to adapter
        '''
        self.logger = logger
        self._running = True  # 用于控制线程启停, 使用self.terminate()可以终止线程
        self.ADAPTER_TOPIC = "from_adapter/extensions"  # message topic: the message from adapter
        self.SCRATCH_TOPIC = "from_scratch/extensions"  # message topic: the message from scratch
        if name:
            self.name = name
        else:
            self.name = type(self).__name__
        self.receive_loop_idle_addition = receive_loop_idle_addition
        self.external_message_processor = external_message_processor
        self.connect_time = connect_time
        self.adapter_exists = False
        if codelab_adapter_ip_address:
            self.codelab_adapter_ip_address = codelab_adapter_ip_address
        else:
            # check for a running CodeLab Adapter
            for pid in psutil.pids():
                p = psutil.Process(pid)
                try:
                    p_command = p.cmdline()
                except psutil.AccessDenied:
                    # occurs in Windows - ignore
                    continue
                try:
                    if any('codelab' in s.lower() for s in p_command):
                        self.adapter_exists = True
                    else:
                        continue
                except UnicodeDecodeError:
                    continue

            if not self.adapter_exists:
                raise RuntimeError(
                    'CodeLab Adapter is not running - please start it.')
            # determine this computer's IP address
            self.codelab_adapter_ip_address = '127.0.0.1'

        self.subscriber_port = subscriber_port
        self.publisher_port = publisher_port
        self.loop_time = loop_time

        print('\n************************************************************')
        print('CodeLab Adapter IP address: ' + self.codelab_adapter_ip_address)
        print('Subscriber Port = ' + self.subscriber_port)
        print('Publisher  Port = ' + self.publisher_port)
        print('Loop Time = ' + str(loop_time) + ' seconds')
        print('************************************************************')

        # establish the zeromq sub and pub sockets and connect to the adapter
        self.context = zmq.Context()
        self.subscriber = self.context.socket(zmq.SUB)
        connect_string = "tcp://" + self.codelab_adapter_ip_address + ':' + self.subscriber_port
        self.subscriber.connect(connect_string)

        self.publisher = self.context.socket(zmq.PUB)
        connect_string = "tcp://" + self.codelab_adapter_ip_address + ':' + self.publisher_port
        self.publisher.connect(connect_string)

        # Allow enough time for the TCP connection to the adapter complete.
        time.sleep(self.connect_time)
        self.set_subscriber_topic(self.SCRATCH_TOPIC)

    def __str__(self):
        return self.name

    def publish(self, message):
        assert isinstance(message, dict)
        topic = message.get('topic')
        payload = message.get("payload")
        if not topic:
            topic = self.ADAPTER_TOPIC
        self.logger.debug(
            f"{self.name} publish: topic: {topic} payload:{payload}")

        self.publish_payload(payload, topic)

    def get_extension_id(self):
        if hasattr(self, 'EXTENSION_ID'):
            return self.EXTENSION_ID
        else:
            return self.name

    def pub_notification(self, content, topic="notification", type="info"):
        '''
        type
            ERROR
            INFO
        {
            topic: "from_adapter/extensions/notification"
            payload: {
                content:
            }
        }
        '''
        extension_id = self.get_extension_id()
        payload = {"type": "error", "extension_id": extension_id}
        payload["content"] = content
        self.publish_payload(payload, topic)

    def pub_status(self, statu):
        topic = ADAPTER_TOPIC + "/status"
        extension_id = self.get_extension_id()
        payload = {"extension_id": extension_id}
        payload["content"] = statu
        self.publish_payload(payload, topic)

    def is_running(self):
        return self._running

    def set_subscriber_topic(self, topic):
        if not type(topic) is str:
            raise TypeError('Subscriber topic must be string')

        self.subscriber.setsockopt(zmq.SUBSCRIBE, topic.encode())

    def publish_payload(self, payload, topic=''):
        if not type(topic) is str:
            raise TypeError('Publish topic must be string', 'topic')

        # create message pack payload
        message = msgpack.packb(payload, use_bin_type=True)

        pub_envelope = topic.encode()
        self.publisher.send_multipart([pub_envelope, message])

    def receive_loop(self):
        """
        This is the receive loop for receiving sub messages.
        """
        while True:
            try:
                data = self.subscriber.recv_multipart(zmq.NOBLOCK)  # NOBLOCK
                topic = data[0].decode()
                payload = msgpack.unpackb(data[1], raw=False)
                self.message_handle(topic, payload)
            # if no messages are available, zmq throws this exception
            except zmq.error.Again:
                try:
                    if self.receive_loop_idle_addition:
                        self.receive_loop_idle_addition()
                    time.sleep(self.loop_time)
                except KeyboardInterrupt:
                    self.clean_up()
                    raise KeyboardInterrupt
            '''
            except msgpack.exceptions.ExtraData as e:
                self.logger.error(str(e))
            '''

    def receive_loop_as_thread(self):
        threaded(self.receive_loop)()

    def message_handle(self, topic, payload):
        """
        Override this method with a custom adapter message processor for subscribed messages.
        """
        if self.external_message_processor:
            self.external_message_processor(topic, payload)
        else:
            pass
            # print('message_handle method should provide implementation in subclass.', topic, payload)

    def clean_up(self):
        """
        Clean up before exiting.
        """
        self.publisher.close()
        self.subscriber.close()
        self.context.term()

    def terminate(self):
        '''
        stop thread
        '''
        self._running = False
        time.sleep(0.1)
        self.clean_up()
        self.logger.info(f"{self} terminate!")
