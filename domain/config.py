class config(object):
    FullPath : str = None
    Values : {} = None

    ## Class initializer
    def __init__(self, path: ""):
        self.FullPath = path
        self.Values = {}
        pass
    
    def addValue(self, key, value):
        self.Values[key] = value
        pass
    
    def removeValue(self, key, value):
        self.Values.pop(key, value)
        pass
    
    def getValue(self, key):
        if len(self.Values) > 0:
            return self.Values.get(key, None)
            pass
        return None
        pass
    pass