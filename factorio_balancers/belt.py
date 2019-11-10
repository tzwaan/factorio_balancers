

class Belt():
    def __init__(self, size=100, inp=None, out=None):
        self.size = size
        self.inp = 0
        self.out = 0

    def add(self, amount):
        if self.inp + amount > self.size:
            rest = self.inp + amount - self.size
            self.inp = self.size
            return rest
        else:
            self.inp += amount
            return 0

    def provide(self, amount=None):
        if amount is None or amount > self.size:
            amount = self.size
        self.inp = amount
        return amount

    def fill(self):
        self.inp = self.size
        self.out = self.size

    def clear(self):
        self.inp = 0
        self.out = 0

    def drain(self):
        amount = self.out
        self.out = 0
        percentage = (amount / self.size) * 100
        return amount, percentage

    def transfer(self):
        output = self.inp + self.out
        if output > self.size:
            self.out = self.size
            self.inp = output - self.size
        else:
            self.out = output
            self.inp = 0
