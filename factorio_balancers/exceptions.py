

class EntityError(Exception):
    def __init__(self, *args, message="", **kwargs):
        super().__init__(*args, **kwargs)
        self.nr = len(args)
        self.message = message

    def __repr__(self):
        result = "<{} (".format(type(self).__name__)
        if self.message != "":
            result += "{}: ".format(self.message)
        for arg in self.args:
            result += "{}, ".format(arg)
        result += ")>"
        return result

    def __eq__(self, other):
        if len(self.args) != len(other.args):
            return False
        for arg in self.args:
            if arg not in self.args:
                return False
        return True


class IllegalEntity(EntityError):
    pass


class IllegalEntities(EntityError):
    def __repr__(self):
        if self.message != "":
            message = "{}\n".format(self.message)
        else:
            message = ""
        result = "IllegalEntities ({message}Number of errors: {nr},".format(
            nr=self.nr, message=message)
        for exception in self.args:
            result += "\n    {}".format(repr(exception))
        result += ")"
        return result


class IllegalConfiguration(EntityError):
    pass


class IllegalConfigurations(EntityError):
    def __repr__(self):
        if self.message != "":
            message = "{}\n".format(self.message)
        else:
            message = ""
        result = "IllegalConfigurations ({message}Number of errors: {nr}," \
            .format(nr=self.nr, message=message)
        for exception in self.args:
            result += "\n    {}".format(repr(exception))
        result += ")"
        return result
