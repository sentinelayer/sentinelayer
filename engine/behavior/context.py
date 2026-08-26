class ApplicationContext:
    def __init__(self):
        self.context = {}

    def set(self, key: str, value: any):
        self.context[key] = value

    def get(self, key: str):
        return self.context.get(key)

    def get_all(self):
        return self.context.copy()
