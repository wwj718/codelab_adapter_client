# HA
from .base import AdapterNode
from codelab_adapter_client.topic import *


class HANode(AdapterNode):
    '''
    使用继承的目的是让新手获得专家的能力 -- alan kay
    real playing

    todo 获取设备状态
    '''

    def __init__(self, *args, mode="rpi", **kwargs):
        '''
        mode rpi/local
        '''
        if mode:
            kwargs["codelab_adapter_ip_address"] = "rpi.codelab.club"
        super().__init__(*args, **kwargs)
        self.TOPIC = TO_HA_TOPIC  # 需放在super初始化之后
        self.set_subscriber_topic(FROM_HA_TOPIC)
        self._id = 1

    def call_service(self,
                     domain="light",
                     service="turn_off",
                     entity_id="light.yeelight1"):
        content = {
            "id": self._id,
            "type": "call_service",
            "domain": domain,
            "service": service,
            "service_data": {
                "entity_id": entity_id
            }
        }
        self._id += 1
        message = self.message_template()
        message['payload']['content'] = content
        self.publish(message)

    def message_handle(self, topic, payload):
        '''
        '''
        if topic == FROM_HA_TOPIC:
            # HA部分只订阅了状态变化事件
            content = payload.get("content")
            event_type = content["type"]
            if event_type == "event":
                data = content["event"]["data"]
                entity_id = data["entity_id"]
                new_state = data["new_state"]
                state = new_state["state"]
                # print(entity_id, state)
                '''
                with open('/tmp/neverland.json', 'w+') as logfile:
                        print(payload, file=logfile)
                        # 在类中做 解析状态变化， 翻译scratch中的做法
                        # todo: 使用正则处理，以门窗感应器为例
                        # "friendly_name": "门窗感应器",
                        # "state": "off"
                        # "state": "on"
                '''
                if "door" in entity_id:
                    print("door_sensor event")
                    door_window_sensor_state = state
                    print(entity_id, door_window_sensor_state)
