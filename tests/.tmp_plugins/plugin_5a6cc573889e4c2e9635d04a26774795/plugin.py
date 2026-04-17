class DemoPlugin:
    def get_tools(self):
        return ['tool-a']
    def get_commands(self):
        return ['cmd-a']
    def get_hooks(self):
        return {'event.a': [lambda payload: payload]}

def get_plugin():
    return DemoPlugin()