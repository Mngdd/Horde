import math
import random

import pygame

from main import projectiles_group
from projectile import Projectile


class Weapon(pygame.sprite.Sprite):
    """
    оружия: 
    дальники: пистолет, шелли, байрон ...
    ближники: катана, топор, палка ...
    написаны в порядке убывания, типо катана самый мощный ближник и тп
    """

    def __init__(self, *groups):
        super().__init__(*groups)
        self.curr_mag_ammo: int = 0  # сколько патрон ща в магазе
        self.mag_capacity: int = 0  # сколько влазит в магаз
        self.ammo_max: int = 0  # сколько можно хранить патрон для этого оружия(без учета магаза)
        # (мб переделать типа патроны не индивидуально хранятся, а в инвентаре)
        self.all_ammo_current: int = 0  # скока ща всего патрон (без учета магаза)
        self.fire_rate: float = 0.0  # темп

        self.name: str = 'NONE'
        self.rarity = None  # типа редкое\легендарное\эпичное и тп TODO: ДОБАВИТЬ РЕДКОСТЬ
        self.cooldown: float = 0.0  # кулдаун собсна В СЕКУНДАХ(через time делать потомучт буду)

    @staticmethod
    def normalize_vector(vector):
        """
        расстояние между двумя точками
        """
        if vector == [0, 0]:
            return [0, 0]
        pythagoras = math.sqrt(vector[0] * vector[0] + vector[1] * vector[1])
        return vector[0] / pythagoras, vector[1] / pythagoras

    @staticmethod
    def rotate_vector(vector, angle):  # corner это не тот угол xD
        """
        это тоже расстояние между двумя точками, только тут еще разброс на какой-то угол
        """
        result_vector = (vector[0] * math.cos(angle) - vector[1] * math.sin(angle),
                         vector[0] * math.sin(angle) + vector[1] * math.cos(angle))
        return result_vector

    def shoot(self, user, mouse_pos):
        """
        выстрел оружия
        """
        pass


class Gun(Weapon):
    def __init__(self, *groups):
        super().__init__(*groups)
        self.weapon_cooldown = 0.2  # тут задержка какая-то, оружие же нагревается
        self.spread = 10  # разброс

    def shoot(self, user, mouse_pos):
        current_time = pygame.time.get_ticks()
        if self.curr_mag_ammo == 0:  # тип перезарядка
            if current_time - 1 > self.cooldown:
                self.curr_mag_ammo = 100
            else:
                return

        self.curr_mag_ammo -= 1  # минус патрон
        if current_time - self.last_shot > self.weapon_cooldown:
            direction = (mouse_pos[0] - user.pos[0], mouse_pos[1] - user.pos[1]) \
                if mouse_pos != user.pos else (1, 1)
            self.last_shot = current_time
            corner = math.radians(random.random() * self.spread - self.spread / 2)
            projDir = super().rotate_vector(direction, corner)
            # тут кароче надо как-то вызвать уже projectile  
            bullet = Projectile(user.pos, super().normalize_vector(projDir), 15, 1000, (255, 0, 0), projectiles_group)


class SpreadGun(Weapon):
    """
    как шелли стреляет
    """

    def __init__(self):
        super().__init__()
        self.weapon_cooldown = 750
        self.spread = 75
        self.count_bullets = 7  # сколько пуль в разбросе

    def shoot(self, user, mousePos, *groups):
        super().__init__(*groups)
        currentTime = pygame.time.get_ticks()
        if self.curr_mag_ammo == 0:  # тип перезарядка
            if currentTime - self.last_shot > self.cooldown:
                self.curr_mag_ammo = 100
            else:
                return

        self.curr_mag_ammo -= self.count_bullets  # минус патроны
        if currentTime - self.last_shot > self.weapon_cooldown:
            direction = (mousePos[0] - user.pos[0], mousePos[1] - user.pos[1]) \
                if mousePos != user.pos else (1, 1)
            self.last_shot = currentTime
            arcDifference = self.spread / (self.count_bullets - 1)
            for proj in range(self.count_bullets):
                corner = math.radians(arcDifference * proj - self.spread / 2)
                projDir = super().rotate_vector(direction, corner)
            # тут кароче надо как-то вызвать уже projectile  
            bullet = Projectile(user.pos, super().normalize_vector(projDir), 6, 1000, (255, 0, 0), projectiles_group)


class FreezeGun(Weapon):
    # Доделать торможение!!!
    def __init__(self, *groups):
        super().__init__(*groups)

        self.weapon_cooldown = 50
        # мне кажется нужно тут делать большую задержку, тип оружие имбовое и ему нужно много времени
        # но урона у врагов он забирает тип много
        self.spread = 5  # разброс маленький
        # кароче будет работать как у байрона в бравл старсе

    def shoot(self, user, mousePos):
        currentTime = pygame.time.get_ticks()
        if self.curr_mag_ammo == 0:  # тип перезарядка
            if currentTime - self.last_shot > self.cooldown:
                self.curr_mag_ammo = 100
            else:
                return

        self.curr_mag_ammo -= 1  # минус патрон
        if currentTime - self.last_shot > self.weapon_cooldown:
            direction = (mousePos[0] - user.pos[0], mousePos[1] - user.pos[1]) \
                if mousePos != user.pos else (1, 1)
            self.last_shot = currentTime
            corner = math.radians(random.random() * self.spread - self.spread / 2)
            projDir = super().rotate_vector(direction, corner)
            # тут кароче надо как-то вызвать уже projectile  
            bullet = Projectile(user.pos, super().normalize_vector(projDir), 10, 1000, (255, 0, 0), projectiles_group)


class Stick(Weapon):
    """
    самый юзлесс ближник, думаю, можно давать его в начале игры
    (типо при спавне игрока валяется рядом или что-то такое?)
    снимает мало хп, дальность средняя
    """

    def __init__(self, *groups):
        super().__init__(*groups)
        ...


class Katana(Weapon):
    """
    самый мощни, снимает много хп и дальность самая большая из ближников
    """

    def __init__(self, *groups):
        super().__init__(*groups)
        ...


class Axe(Weapon):
    """
    средняк, лучше палки,хуже катаны
    дальность меньше палки, но урона снимает много
    """

    def __init__(self, *groups):
        super().__init__(*groups)
        ...
