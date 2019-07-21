'''
Usage
    pip install codelab_adapter_client
'''
import time
import logging
from codelab_adapter_client import AdapterNode, threaded

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)


class EIMNode(AdapterNode):
    '''
    Everything Is Message
    '''

    def __init__(self):
        super().__init__()
        self.logger = logger
        # self.EXTENSION_ID = "eim" # default: eim

    def extension_message_handle(self, topic, payload):
        print(topic, payload, type(payload))
        if type(payload) == str:
            self.logger.info(f'scratch eim message:{payload}')
            return
        elif type(payload) == dict:
            self.logger.info(f'eim message:{payload}')
            self.publish({"payload": payload})

    def run(self):
        i = 0
        while self._running:
            message = {"payload": {"content": str(i)}}  # topic可选
            self.publish(message)
            time.sleep(1)
            i += 1


if __name__ == "__main__":
    try:
        node = EIMNode()
        node.receive_loop_as_thread()  # run extension_message_handle, noblock(threaded)
        node.run()
    except KeyboardInterrupt:
        node.terminate()  # Clean up before exiting.
