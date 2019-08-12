from domain.config import config 
from abc import ABC
import json

class base_config_manager(ABC):
    configuration: config = None

    def __init__(self, path, jsonPathToRead):
        if(self.configuration is None):
            self.configuration = config(path)
            
            val = json.loads(open(self.configuration.FullPath).read())
            valAux = {}

            if str(jsonPathToRead).__len__() > 0:
                valAux = val[jsonPathToRead]
            else:
                valAux = val

            if valAux is not None:
                for k, v in valAux.items():
                    self.configuration.addValue(k, v)                
        pass  
    pass