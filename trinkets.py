class Trinket:  # точно так же как и перки, но получает игрок во время игры и только на 1 игру(потом заново покупать)
    def __init__(self):
        self.name = None
        self.description = None

    def use(self, Player):
        pass


class AKIMBO(Trinket):
    def __init__(self):
        self.name = 'Парное оружие'
        self.description = 'чиста как гееенгста ходить с двумя пушками еуу'

    def use(self, Player):
        Player.trinkets['AKIMBO'] = True


class VAMPIRE_1(Trinket):
    def __init__(self):
        self.name = 'вампирисзсм'
        self.description = 'за 15 убитых врагов восстанавливает 10 хп'

    def use(self, Player):
        Player.trinkets['VAMPIRE_1'] = True


class FAST_SHOOT_1(Trinket):
    def __init__(self):
        self.name = 'ну типа чтоб стрелят быстро'
        self.description = 'темп стрельбы и ударов мили оружием выше'

    def use(self, Player):
        Player.trinkets['FAST_SHOOT_1'] = True


all_trinkets = {'AKIMBO': False, 'VAMPIRE_1': False, 'FAST_SHOOT_1': False}