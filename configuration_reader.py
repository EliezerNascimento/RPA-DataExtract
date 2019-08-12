import base_classes.base_config_manager

class reader(base_classes.base_config_manager.base_config_manager):
    # Class initializer
    def __init__(self, path, jsonPathToRead):
        super().__init__(path, jsonPathToRead)
        pass
    
    # Gets the value from a given key
    def getValue(self, key, defaultValue = None):
        value = self.configuration.getValue(key)
        
        if value is None:
            return defaultValue

        return value 
    pass