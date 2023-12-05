import _thread

class IEntity:
    def __init__(self, code, register, store, value_length):
        self.code = code
        self.register = register
        self.store = store
        self.value_length = value_length
        self.value = 0

    def set_to_store(self, new_value):
        self.store.setValues(self.code, self.register, new_value)

    def get_from_store(self):
        return self.store.getValues(self.code, self.register, self.value_length)

    def set_value(self, new_value):
        pass

    def get_value(self):
        pass

class SyncEntity(IEntity):
    def __init__(self, code, register, value, store, value_length):
        super().__init__(code, register, value, store, value_length)
        self.sync =  _thread.allocate_lock()

    def set_to_store(self, new_value):
        self.sync.acquire()
        self.store.setValues(self.code, self.register, new_value)
        self.sync.release()

    def get_from_store(self):
        self.sync.acquire()
        value = self.getValues(self.code, self.register, self.value_length)
        self.sync.release()
        return value