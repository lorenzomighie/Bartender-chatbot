class Bar:
    """Class that models the drinks available in the bar.
    Attributes:
        drinks (List[Drink]): A list of the available drinks in the bar.
    """

    def __init__(self):
        self.drinks = {}

    def get_drinks(self, category=None):
        """Returns the list of drinks available in the bar.
        Keyword Args:
            category (Optional[str]): Category of drinks (default None).
        Returns:
            List[Drink]: List of drinks
        """
        if not category:
            lst = []
            for key in self.drinks:
                lst.extend(self.drinks[key])
            return lst
        else:
            return self.drinks[category]

    def get_drink(self, name):
        for drink in self.get_drinks():
            if drink.name == name:
                return drink

    def add_drink(self, drink):
        if drink.category not in self.drinks:
            self.drinks[drink.category] = [drink]
        else:
            self.drinks[drink.category].append(drink)


class Drink:
    CATEGORY = ['beer', 'wine']

    def __init__(self, name, category, price):
        self.name = name
        self.category = category
        self.price = price
