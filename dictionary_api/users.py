
class SimpleUser:
    """
    Упрощённое представление аутентифицированного пользователя.

    Атрибуты:
        - id (UUID): Уникальный идентификатор пользователя.
        - username (str): Имя пользователя.
        - is_authenticated (bool): Флаг, указывающий, что пользователь аутентифицирован.
    """
    def __init__(self, payload):
        self.id = payload.get('user_id')
        self.username = payload.get('username')
        self.is_authenticated = True


class AnonymousUser:
    """
    Представление анонимного (неаутентифицированного) пользователя.

    Атрибуты:
        - is_authenticated (bool): Флаг, указывающий, что пользователь не аутентифицирован.
    """
    def __init__(self):
        self.is_authenticated = False
