import math
import random
from threading import Timer
import time
import pygame

from main import load_image


class Weapon(pygame.sprite.Sprite):  # каркас мили и дальнего оружия
    AUTO = 'AUTO'
    SINGLE = 'SINGLE'
    BURST = 'BURST'  # типы стрельбы
    SHOTGUN = 'SHOTGUN'
    DRAW_SIZE = (86, 44)
    SHOOT = 'SHOOT'
    RELOAD = 'RELOAD'
    RELOAD_FINISHED = 'RELOAD_FINISHED'
    NO_AMMO = 'NO_AMMO'

    def __init__(self, x, y, *groups):
        super().__init__(*groups)
        self.damage_range = (1, 2)  # min и max урон
        self.curr_mag_ammo: int = 0  # сколько патрон ща в магазе
        self.mag_capacity: int = 0  # сколько влазит в магаз
        self.ammo_max: int = 0  # сколько можно хранить патрон для этого оружия(без учета магаза)
        # (мб переделать типа патроны не индивидуально хранятся, а в инвентаре)
        self.all_ammo_current: int = 0  # скока ща всего патрон (без учета магаза)
        self.spread: float = 0.0  # разброс
        self.reload_time: float = 0.0  # время перезарядлки оружия
        self.name: str = 'NONE'
        self.sounds: dict = {}
        self.rarity = None  # типа редкое\легендарное\эпичное и тп TODO: ДОБАВИТЬ РЕДКОСТЬ
        self.shoot_type = Weapon.SINGLE
        self.cooldown: float = 0.0  # темп собсна В СЕКУНДАХ(через time делать потомучт буду)
        self.can_shoot: bool = True  # если нет патрон/перезарядка/кулдаун, то фолс
        self.reloading = False  # чтоб игрок не спамил перезарядкой в момент перезарядки
        self.frames = []
        self.cur_frame = 5  # номер кадра с картинкой оружия
        self.cut_sheet(load_image("weapons/weapons1.png"), 10, 20)
        self.image = pygame.transform.scale(self.frames[self.cur_frame], Weapon.DRAW_SIZE)
        self.angle: int = 0  # угол поворота
        self.noammotiming = time.time()  # чтоб не спамить

        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.pos = self.rect.topleft

    def timer(self, time, func):
        t_timer = Timer(time, func)
        t_timer.start()

    def cooldown_finish(self):
        self.can_shoot = True

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

    def shoot(self, user, mouse_pos, looking_at):
        """
        выстрел оружия
        """
        pass

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def pick_up(self, user):  # удаляем с земли, даем игроку
        user.available_weapons.append(self)
        user.equipped_weapon = len(user.available_weapons) - 1

    def rot_center(self, angle):
        self.image = pygame.transform.rotate(self.image, angle)

    def init_sounds(self):
        self.sounds = {Weapon.SHOOT: self.load_sound('hl2_shotgun.mp3', 0.5),
                       Weapon.RELOAD: self.load_sound('hl2_shotgun_reload.mp3', 0.5),
                       Weapon.RELOAD_FINISHED: self.load_sound('hl2_shotgun_reload_finished.mp3', 0.5),
                       Weapon.NO_AMMO: self.load_sound('no_ammo.mp3', 0.5)}

    def load_sound(self, name: str, vol: float=1):
        tmp = pygame.mixer.Sound("data/weapons/" + name)
        tmp.set_volume(vol)
        return tmp


class Gun(Weapon):
    """
        каркас стреляющего оружия
    """

    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups)
        self.ammo_lifetime: int = 10
        self.curr_mag_ammo: int = 15  # сколько патрон ща в магазе
        self.mag_capacity: int = 15  # сколько влазит в магаз
        self.ammo_max: int = 100  # сколько можно хранить патрон для этого оружия(без учета магаза)
        # TODO: (мб переделать типа патроны не индивидуально хранятся, а в инвентаре)
        self.all_ammo_current: int = 32  # скока ща всего патрон (без учета магаза)
        self.spread: float = 6.8  # разброс
        self.reload_time = 3.0
        self.name: str = 'DEV GUN'
        self.bullets_per_shot: int = 6  # кол-во дробинок при выстреле из дробаша
        self.rarity = None  # типа редкое\легендарное\эпичное и тп TODO: ДОБАВИТЬ РЕДКОСТЬ
        self.shoot_type = Weapon.BURST
        self.burst_count_max = 4  # скок патров за берст улетает
        self.burst_curr = 4  # скок берстом еще вылетит
        self.burst_timer: float = 0.3  # кулдаун между кучковыми выстрелами
        self.cooldown: float = 0.025  # кулдаун собсна В СЕКУНДАХ(через time делать потомучт буду)
        self.can_shoot: bool = True  # если нет патрон/перезарядка/кулдаун, то фолс
        self.burst_can_shoot: bool = True

        self.cur_frame = 6  # номер кадра с картинкой оружия
        self.image = pygame.transform.scale(self.frames[self.cur_frame], Weapon.DRAW_SIZE)

        self.init_sounds()  # ИНИЦИАЛИЗАЦИЯ ЗВУКОВ ОРУЖИЯ, БЕЗ ЭТОЙ СТРОКИ БУДЕТ ВЫЛЕТ

    def burst_cooldown_finish(self):
        self.burst_curr = self.burst_count_max
        self.burst_can_shoot = True

    def shoot(self, user, mouse_pos, cam_pos):
        # current_time = pygame.time.get_ticks()  # а оно надо?
        if self.can_shoot and self.burst_can_shoot and self.curr_mag_ammo > 0:
            if self.shoot_type == Weapon.BURST:
                if self.burst_curr == 0:
                    self.burst_can_shoot = False
                    self.timer(self.burst_timer, self.burst_cooldown_finish)
                else:
                    self.burst_curr -= 1
            elif self.shoot_type == Weapon.SINGLE:
                self.burst_can_shoot = False
                self.timer(self.burst_timer, self.burst_cooldown_finish)
            self.curr_mag_ammo -= 1  # минус патрон
            self.sounds[Weapon.SHOOT].play()
            direction = (mouse_pos[0] - user.pos[0], mouse_pos[1] - user.pos[1]) \
                if mouse_pos != user.pos else (1, 1)  # куда стреляем
            direction += cam_pos
            if self.shoot_type == Weapon.SHOTGUN:
                bullets = []
                self.can_shoot = False
                self.timer(self.cooldown, self.cooldown_finish)
                for b in range(1, self.bullets_per_shot + 1):
                    angle = math.radians(1 / self.bullets_per_shot * b * self.spread * random.random() -
                                         self.spread / 2 * random.choice([-1, 1]))  # разброс случайны
                    angled_direction = self.rotate_vector(direction, angle)  # траектория пули с учетом разброса
                    bullets.append((list(user.rect.center)[:], super().normalize_vector(angled_direction), 5, self.ammo_lifetime,
                                    random.randrange(*self.damage_range)))
                return bullets
            else:
                angle = math.radians(random.random() * self.spread -
                                     self.spread / 2 * random.choice([-1, 1]))  # разброс случайны
                angled_direction = self.rotate_vector(direction, angle)  # траектория пули с учетом разброса

                # спавним пулю и передаем ей юзера, направление, скорость, длительность полета
                # и спрайт-группу
                self.can_shoot = False
                self.timer(self.cooldown, self.cooldown_finish)
                print('SHOOT', self.curr_mag_ammo, self.all_ammo_current)
                return list(user.rect.center)[:], super().normalize_vector(angled_direction), 5, self.ammo_lifetime, \
                       random.randrange(*self.damage_range)
        if self.curr_mag_ammo == 0:
            if time.time() - self.noammotiming > 0.5:
                self.noammotiming = time.time()
                self.sounds[Weapon.NO_AMMO].play()
            return print('NO AMMO')

    def reload(self):
        if self.curr_mag_ammo == self.mag_capacity:
            return
        if self.reloading is False and self.all_ammo_current > 0:
            self.sounds[Weapon.RELOAD].play()
            self.reloading = True
            self.can_shoot = False
            self.timer(self.reload_time, self.reload)
        else:
            self.sounds[Weapon.RELOAD].stop()
            self.sounds[Weapon.RELOAD_FINISHED].play()
            tmp = (self.mag_capacity - self.curr_mag_ammo) % self.all_ammo_current
            self.curr_mag_ammo += tmp
            self.all_ammo_current -= tmp
            self.reloading = False
            self.can_shoot = True


class MachineGun(Gun):
    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups)
        self.curr_mag_ammo: int = 15
        self.mag_capacity: int = 15
        self.ammo_max: int = 100
        self.all_ammo_current: int = 32
        self.spread: float = 6.8
        self.reload_time = 3.0
        self.name: str = 'machine gun class'
        self.rarity = None
        self.shoot_type = Weapon.AUTO
        self.cooldown: float = 0.2
        self.can_shoot: bool = True

        self.cur_frame = 6
        self.image = pygame.transform.scale(self.frames[self.cur_frame], Weapon.DRAW_SIZE)

        self.init_sounds()

    def init_sounds(self):
        self.sounds = {Weapon.SHOOT: self.load_sound('rifle_shoot.mp3', 0.2),
                       Weapon.RELOAD: self.load_sound('ak_reload.mp3', 0.5),
                       Weapon.RELOAD_FINISHED: self.load_sound('ak_reload_finished.mp3', 0.5),
                       Weapon.NO_AMMO: self.load_sound('no_ammo.mp3', 0.5)}


class PistolLikeGun(Gun):
    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups)
        self.curr_mag_ammo: int = 15
        self.mag_capacity: int = 15
        self.ammo_max: int = 100
        self.all_ammo_current: int = 32
        self.spread: float = 6.8
        self.reload_time = 3.0
        self.name: str = 'pistol class'
        self.rarity = None
        self.shoot_type = Weapon.SINGLE
        self.cooldown: float = 0.2
        self.can_shoot: bool = True

        self.cur_frame = 6
        self.image = pygame.transform.scale(self.frames[self.cur_frame], Weapon.DRAW_SIZE)

        self.init_sounds()

    def init_sounds(self):
        self.sounds = {Weapon.SHOOT: self.load_sound('hl2_usp.mp3', 0.3),
                       Weapon.RELOAD: self.load_sound('usp_reload.mp3'),
                       Weapon.RELOAD_FINISHED: self.load_sound('usp_reload_finished.mp3'),
                       Weapon.NO_AMMO: self.load_sound('no_ammo.mp3', 0.5)}


class BurstGun(Gun):
    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups)
        self.curr_mag_ammo: int = 15
        self.mag_capacity: int = 15
        self.ammo_max: int = 100
        self.all_ammo_current: int = 32
        self.spread: float = 6.8
        self.reload_time = 3.0
        self.name: str = 'burst gun class'
        self.rarity = None
        self.shoot_type = Weapon.BURST
        self.burst_count_max = 4
        self.burst_curr = 4
        self.burst_timer: float = 0.3
        self.cooldown: float = 0.025
        self.can_shoot: bool = True
        self.burst_can_shoot: bool = True

        self.cur_frame = 6
        self.image = pygame.transform.scale(self.frames[self.cur_frame], Weapon.DRAW_SIZE)

        self.init_sounds()

    def init_sounds(self):
        self.sounds = {Weapon.SHOOT: self.load_sound('rifle_shoot.mp3', 0.2),
                       Weapon.RELOAD: self.load_sound('ak_reload.mp3'),
                       Weapon.RELOAD_FINISHED: self.load_sound('ak_reload_finished.mp3'),
                       Weapon.NO_AMMO: self.load_sound('no_ammo.mp3', 0.5)}


class Shotgun(Gun):
    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups)
        self.curr_mag_ammo: int = 2
        self.mag_capacity: int = 15
        self.ammo_max: int = 100
        self.all_ammo_current: int = 32
        self.spread: float = 16.8
        self.reload_time = 3.0
        self.name: str = 'shotgun class'
        self.rarity = None
        self.shoot_type = Weapon.SHOTGUN
        self.burst_count_max = 4
        self.burst_curr = 4
        self.burst_timer: float = 0.3
        self.cooldown: float = 0.4
        self.can_shoot: bool = True
        self.burst_can_shoot: bool = True

        self.cur_frame = 6
        self.image = pygame.transform.scale(self.frames[self.cur_frame], Weapon.DRAW_SIZE)

        self.init_sounds()

    def init_sounds(self):
        self.sounds = {Weapon.SHOOT: self.load_sound('hl2_shotgun.mp3', 0.4),
                       Weapon.RELOAD: self.load_sound('hl2_shotgun_reload.mp3', 0.5),
                       Weapon.RELOAD_FINISHED: self.load_sound('hl2_shotgun_reload_finished.mp3', 0.5),
                       Weapon.NO_AMMO: self.load_sound('no_ammo.mp3', 0.5)}


class Melee(Weapon):
    def __init__(self, *groups):
        super().__init__(*groups)
        self.init_sounds()

    def hit_sound(self):
        random.choice(self.sounds).play()

    def init_sounds(self):
        self.sounds = [self.load_sound(f'melee_hit{i}.mp3') for i in range(1, 4)]


class EnemyMelee(Melee):
    def __init__(self, *groups):
        super().__init__(*groups)


# вот тут сами оружия делаю
class Usp(PistolLikeGun):
    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups)
        self.damage_range = (10, 15)
        self.ammo_lifetime = 900
        self.curr_mag_ammo: int = 15
        self.mag_capacity: int = 15
        self.ammo_max: int = 15*4
        self.all_ammo_current: int = 15*4
        self.spread: float = 6.8
        self.reload_time = 1.7
        self.name: str = 'USP-S'
        self.rarity = None
        self.cooldown: float = 0.1
        self.price: int = 10

        self.cur_frame = 21
        self.image = pygame.transform.scale(self.frames[self.cur_frame], Weapon.DRAW_SIZE)
        self.init_sounds()


class Spas12(Shotgun):
    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups)
        self.damage_range = (30, 45)
        self.ammo_lifetime = 300
        self.curr_mag_ammo: int = 12
        self.mag_capacity: int = 12
        self.ammo_max: int = 12*4
        self.all_ammo_current: int = 12*4
        self.spread: float = 6.8
        self.reload_time = 2.0
        self.name: str = 'SPAS-12'
        self.rarity = None
        self.cooldown: float = 0.8
        self.price: int = 40

        self.cur_frame = 73
        self.image = pygame.transform.scale(self.frames[self.cur_frame], Weapon.DRAW_SIZE)
        self.init_sounds()


class M16(BurstGun):
    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups)
        self.ammo_lifetime = 1000
        self.damage_range = (20, 25)
        self.curr_mag_ammo: int = 32
        self.mag_capacity: int = 32
        self.ammo_max: int = 32*3
        self.all_ammo_current: int = 32*3
        self.spread: float = 6.8
        self.reload_time = 3.0
        self.name: str = 'M16'
        self.rarity = None
        self.cooldown: float = 0.2
        self.burst_count_max = 4
        self.burst_curr = 4
        self.burst_timer: float = 0.3
        self.cooldown: float = 0.025
        self.price: int = 30

        self.cur_frame = 104
        self.image = pygame.transform.scale(self.frames[self.cur_frame], Weapon.DRAW_SIZE)
        self.init_sounds()


class AK47(MachineGun):
    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups)
        self.ammo_lifetime = 1000
        self.damage_range = (20, 25)
        self.curr_mag_ammo: int = 24
        self.mag_capacity: int = 24
        self.ammo_max: int = 24*3
        self.all_ammo_current: int = 24*3
        self.spread: float = 6.8
        self.reload_time = 2.0
        self.name: str = 'AK-47'
        self.rarity = None
        self.cooldown: float = 0.1
        self.can_shoot: bool = True
        self.price: int = 50

        self.cur_frame = 134
        self.image = pygame.transform.scale(self.frames[self.cur_frame], Weapon.DRAW_SIZE)
        self.init_sounds()


class Minigun(MachineGun):
    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups)
        self.ammo_lifetime = 1000
        self.damage_range = (30, 35)
        self.curr_mag_ammo: int = 100
        self.mag_capacity: int = 100
        self.ammo_max: int = 500
        self.all_ammo_current: int = 500
        self.spread: float = 6.8
        self.reload_time = 3.0
        self.name: str = 'MINIGUN'
        self.rarity = None
        self.cooldown: float = 0.1
        self.can_shoot: bool = True
        self.price: int = 100

        self.cur_frame = 86
        self.image = pygame.transform.scale(self.frames[self.cur_frame], Weapon.DRAW_SIZE)
        self.init_sounds()


class Awp(PistolLikeGun):
    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups)
        self.ammo_lifetime = 1000
        self.damage_range = (40, 50)
        self.curr_mag_ammo: int = 5
        self.mag_capacity: int = 5
        self.ammo_max: int = 25
        self.all_ammo_current: int = 25
        self.spread: float = 0.25
        self.reload_time = 4
        self.name: str = 'AWP'
        self.rarity = None
        self.cooldown: float = 2
        self.can_shoot: bool = True
        self.price: int = 20

        self.cur_frame = 95
        self.image = pygame.transform.scale(self.frames[self.cur_frame], Weapon.DRAW_SIZE)
        self.init_sounds()
        self.sounds[Weapon.SHOOT] = self.load_sound('awp_shoot.mp3', 0.3)
        self.sounds[Weapon.RELOAD] = self.load_sound('awp_reload.mp3')


# class FreezeGun(Weapon):
#     # Доделать торможение!!!
#     def __init__(self, *groups):
#         super().__init__(*groups)
#
#         self.weapon_cooldown = 50
#         # мне кажется нужно тут делать большую задержку, тип оружие имбовое и ему нужно много времени
#         # но урона у врагов он забирает тип много
#         self.spread = 5  # разброс маленький
#         # кароче будет работать как у байрона в бравл старсе
#
#     def shoot(self, user, mousePos):
#         currentTime = pygame.time.get_ticks()
#         if self.curr_mag_ammo == 0:  # тип перезарядка
#             if currentTime - self.last_shot > self.cooldown:
#                 self.curr_mag_ammo = 100
#             else:
#                 return
#
#         self.curr_mag_ammo -= 1  # минус патрон
#         if currentTime - self.last_shot > self.weapon_cooldown:
#             direction = (mousePos[0] - user.pos[0], mousePos[1] - user.pos[1]) \
#                 if mousePos != user.pos else (1, 1)
#             self.last_shot = currentTime
#             corner = math.radians(random.random() * self.spread - self.spread / 2)
#             projDir = super().rotate_vector(direction, corner)
#             # тут кароче надо как-то вызвать уже projectile
#             bullet = Projectile(user.pos, super().normalize_vector(projDir), 10, 1000, (255, 0, 0), projectiles_group)


purchasable_weapons = [Usp, Spas12, M16, AK47, Minigun, Awp]
