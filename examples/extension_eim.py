'''
EIM: Everything Is Message
Usage
    git clone https://github.com/wwj718/codelab_adapter_client
    pip install codelab_adapter_client
'''
import time
from codelab_adapter_client import AdapterNode


class EIMNode(AdapterNode):
    def __init__(self):
        name = type(self).__name__  # class name
        super().__init__(name)
        self.TOPIC = "adapter/eim"
        self.set_subscriber_topic('adapter/eim')

    def message_handle(self,topic,payload):
        "message processor for subscribed messages."
        print('sub:',topic, payload)

    def run(self):
        while True:
            message = {"topic": self.TOPIC, "payload": "payload"}
            print("pub",message)
            self.publish(message)
            time.sleep(1)

if __name__ == "__main__":
    try:
        node = EIMNode()
        node.receive_loop() # run message_handle, noblock(threaded)
        node.run()
    except KeyboardInterrupt:
        node.clean_up() # Clean up before exiting.
