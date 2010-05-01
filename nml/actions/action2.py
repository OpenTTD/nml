from nml.generic import *

free_action2_ids = range(1, 255)

action2_map = {}

class Action2:
    def __init__(self, feature, name):
        global action2_map
        assert not name in action2_map
        action2_map[name] = self
        self.feature = feature
        self.name = name
        self.num_refs = 0
    
    def write(self, file, size):
        global free_action2_ids
        file.write(str(size + 3) + " 02 ")
        print_bytex(file, self.feature)
        self.id = free_action2_ids.pop()
        print_bytex(file, self.id)
    
    def skip_action7(self):
        return False
    
    def skip_action9(self):
        return False
    
    def skip_needed(self):
        return True

def add_ref(name):
    global action2_map
    if name not in action2_map: raise ScriptError("Referencing unknown action2 id: " + name)
    action2_map[name].num_refs += 1
    return action2_map[name]

def remove_ref(name):
    if name == 'CB_FAILED': return 0
    global action2_map, free_action2_ids
    action2 = action2_map[name]
    id = action2.id
    action2.num_refs -= 1
    if action2.num_refs == 0: free_action2_ids.append(action2.id)
    return id
