import pygame
import math
import random
from main import Projectile

class Weapon(pygame.sprite.Sprite):
    """
    оружие
    """
    def __init__(self, *groups):
        super().__init__(*groups)
        self.curr_mag_ammo = 0  # сколько патрон ща в магазе
        self.mag_capacity = 0  # сколько влазит в магаз
        self.ammo_max = 0  # сколько можно хранить патрон для этого оружия(без учета магаза)
        # (мб переделать типа патроны не индивидуально хранятся, а в инвентаре)
        self.all_ammo_current = 0  # скока ща всего патрон (без учета магаза)
        self.fire_rate = 0.0  # темп
        
        self.name = 'NONE'
        self.rarity = None  # типа редкое\легендарное\эпичное и тп
        self.last_shot = 0
        self.munition = 100 # колво патронов 
        self.munitionTime = 2000 # колво милисекунд, в течении которого оружие перезаряжается
    
    def normalize_vector(vector):
        """
        расстояние между точками, то есть между врагом и юзером
        """
        if vector == [0, 0]:
            return [0, 0]    
        pythagoras = math.sqrt(vector[0]*vector[0] + vector[1]*vector[1])
        return (vector[0] / pythagoras, vector[1] / pythagoras)
    
    @staticmethod
    def rotate_vector(vector, corner):
        """
        это тоже расстояние между врагом и юзером, только тут еще разброс на какой-то угол,
        если мы хотим потом использовать оружие которое стреляет как шелли из бравл старса
        """
        resultVector = (vector[0] * math.cos(corner)
                        - vector[1] * math.sin(corner),
                        vector[0] * math.sin(corner)
                        + vector[1] * math.cos(corner))
        return resultVector

    def shoot(self):
        """
        выстрел оружия
        """
        pass
    

class Gun(Weapon):
    def __init__(self):
        super.__init__()
        self.weapon_cooldown = 100 # тут задержка какая-то, оружие же нагревается
        self.spread = 10  # разброс
    
    def shoot(self, user, mousePos):
        currentTime = pygame.time.get_ticks()
        if self.munition == 0: # тип перезарядка
            if currentTime - self.last_shot > self.munitionTime:
                self.munition = 100
            else:
                return
        
        self.munition -= 1 # минус патрон
        if currentTime - self.last_shot > self.weapon_cooldown:
            direction = (mousePos[0] - user.pos[0], mousePos[1] - user.pos[1]) \
                if mousePos != user.pos else (1, 1)
            self.last_shot = currentTime
            corner = math.radians(random.random()*self.spread - self.spread/2)
            projDir = super().rotate_vector(direction, corner)
            # тут кароче надо как-то вызвать уже projectile  
            Projectile(user.pos, super().normalize_vector(projDir), 6, 1000, (255, 0, 0))
            # это кнш не совсем то, надо доделать


class SpreadGun(Weapon):
    """
    как шелли стреляет
    """
    def __init__(self):
        super().__init__()
        self.weapon_cooldown = 750
        self.spread = 75
        self.count_bullets = 7 # сколько пуль в разбросе
        
    def shoot(self, user, mousePos):
        currentTime = pygame.time.get_ticks()
        if self.munition == 0: # тип перезарядка
            if currentTime - self.last_shot > self.munitionTime:
                self.munition = 100
            else:
                return
        
        self.munition -= self.count_bullets # минус патроны
        if currentTime - self.last_shot > self.weapon_cooldown:
            direction = (mousePos[0] - user.pos[0], mousePos[1] - user.pos[1]) \
                if mousePos != user.pos else (1, 1)
            self.last_shot = currentTime
            arcDifference = self.spread / (self.count_bullets - 1)
            for proj in range(self.count_bullets):
                corner = math.radians(arcDifference*proj - self.spread/2)
                projDir = super().rotate_vector(direction, corner)
            # тут кароче надо как-то вызвать уже projectile  
            Projectile(user.pos, super().normalize_vector(projDir), 6, 1000, (255, 0, 0))
            # это кнш не совсем то, надо доделать
                

