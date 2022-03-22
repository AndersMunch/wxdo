# wxWize wrapper
import wize as iz
from . import deep_object_list

class DeepObjectList(iz.Panel):
    props = iz.Panel.props | set(['param', 'readonly', 'initial_value'])
    positional = ['param', 'initial_value']
    readonly = False
    initial_value = None
    def create_wxwindow(self):
        return self.initfn(deep_object_list.DeepObjectList)(self.parent, self.id, self.param, self.readonly, self.initial_value)
