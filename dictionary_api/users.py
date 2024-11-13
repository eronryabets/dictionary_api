
class SimpleUser:
    def __init__(self, payload):
        self.id = payload.get('user_id')
        self.username = payload.get('username')
        self.is_authenticated = True


class AnonymousUser:
    def __init__(self):
        self.is_authenticated = False
