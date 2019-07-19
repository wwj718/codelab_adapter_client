'''
EIM: Everything Is Message
Usage
    git clone https://github.com/wwj718/codelab_adapter_client
    pip install codelab_adapter_client
'''
import time
from codelab_adapter_client import AdapterNode, threaded


class EIMNode(AdapterNode):
    def __init__(self):
        super().__init__()
        self.EXTENSION_ID = "eim"  # extension_id

    def message_handle(self, topic, payload):
        print(topic, payload, type(payload))
        if type(payload) == str:
            self.logger.info(f'scratch eim message:{payload}')
            return
        if type(payload) == dict:
            extension_id = payload.get('extension_id')
            if extension_id == self.EXTENSION_ID:
                self.logger.info(f'eim message:{payload}')
                self.publish({"payload": payload})

    def run(self):
        i = 0
        while self._running:
            payload = {}
            payload["content"] = str(i)
            payload["extension_id"] = self.EXTENSION_ID
            message = {"payload": payload}
            self.publish(message)
            self.logger.debug(f'pub {message}')
            time.sleep(1)
            i += 1


if __name__ == "__main__":
    try:
        node = EIMNode()
        node.receive_loop_as_thread()  # run message_handle, noblock(threaded)
        node.run()
    except KeyboardInterrupt:
        node.clean_up()  # Clean up before exiting.
