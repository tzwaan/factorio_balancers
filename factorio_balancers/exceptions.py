

class EntityError(Exception):
    def __init__(self, *args, message="", **kwargs):
        super().__init__(*args, **kwargs)
        self.nr = len(args)
        self.message = message

    def __repr__(self):
        result = f"<{type(self).__name__} ("
        if self.message != "":
            result += f"{self.message}: "
        for arg in self.args:
            result += f"{arg}, "
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
            message = f"{self.message}\n"
        else:
            message = ""
        result = f"IllegalEntities ({message}Number of errors: {self.nr},"
        for exception in self.args:
            result += f"\n    {repr(exception)}"
        result += ")"
        return result


class IllegalConfiguration(EntityError):
    pass


class IllegalConfigurations(EntityError):
    def __repr__(self):
        if self.message != "":
            message = f"{self.message}\n"
        else:
            message = ""
        result = f"IllegalConfigurations ({message}Number of errors: {self.nr},"
        for exception in self.args:
            result += f"\n    {repr(exception)}"
        result += ")"
        return result
