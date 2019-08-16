# HA
from .base import AdapterNode
from codelab_adapter_client.topic import *

class HANode(AdapterNode):
    '''
    todo 获取设备状态
        使用future/promise风格
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TOPIC = TO_HA_TOPIC