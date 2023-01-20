class Perk:
    def __init__(self):
        self.name = None
        self.description = None

    def use(self, Player):
        Player.perks.append(self)


class begit(Perk):
    def __init__(self):
        self.name = 'Бегит'
        self.description = 'хоп хоп такой и потом быстро так бежиш ' \
                           'типа усейн болт типа пон'

    def use(self, Player):
        super().use(Player)
        Player.movement_speed *= 2


class sila(Perk):
    def __init__(self):
        self.name = 'Анжумання'
        self.description = 'типа стрелять чтоб мощно так'

    def use(self, Player):
        super().use(Player)
        Player.multipliers['STRENGTH_P'] += 2


class hp(Perk):
    def __init__(self):
        self.name = 'прес качат'
        self.description = 'чтоб хп болш было'

    def use(self, Player):
        super().use(Player)
        Player.health += 100
