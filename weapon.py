import math
import random
from threading import Timer

import pygame

from main import load_image, projectiles_group, screen


class Projectile(pygame.sprite.Sprite):  # пуля сама

    def __init__(self, source, target, speed, lifetime, color, *groups):
        # откуда, куда, скорость, сколько длится жизнь пули, цвет
        super().__init__(*groups)
        self.image = pygame.Surface([4, 4])  # TODO: ПЕРЕПИСАТЬ НА ПНГ КАК У ОРУЖИЯ КРЧ
        self.image.set_colorkey(pygame.Color('black'))
        self.rect = self.image.get_rect(x=source[0], y=source[1])
        pygame.draw.circle(screen, color,
                           (self.rect.width // 2, self.rect.height // 2),
                           self.rect.width // 2)
        self.pos = [source[0], source[1]]
        self.movement_vector = [target[0], target[1]]
        self.speed = speed
        self.lifetime = lifetime
        self.when_created = pygame.time.get_ticks()
        print('BULLET AT ', self.pos)

    def move(self, time):  # размер экрана и время
        if pygame.time.get_ticks() > self.when_created + self.lifetime:
            self.kill()  # пуля исчезает, если время ее жизни истекло
        self.pos[0] += self.movement_vector[0] * self.speed * time
        self.pos[1] += self.movement_vector[1] * self.speed * time
        self.rect.topleft = self.pos
        # я не уверена, по идее это должно давать нам следующую координату
        # TODO: переделать под макс длину жизни пули
        # TODO: или макс длину, за экран ваще по барабану
        if self.pos[0] > screen or self.pos[0] < 0 or \
                self.pos[1] > screen or self.pos[1] < 0:
            self.kill()  # если пуля вышла за пределы экрана - исчезает

    def update(self):
        print('UPDATIN BULLET')
        self.move(2)

    def render(self, surface):
        surface.blit(self.image, self.pos)

    def meet(self, bullet, obj) -> str:
        if pygame.sprite.spritecollide(bullet, obj, False, pygame.sprite.collide_rect):
            return obj.__name__

    def hit(self, bullet, enemy):
        if self.meet(bullet, enemy) == 'Enemy':
            # self.health -= 1 # типо нужно вычитать какое-то колво хп у противника
            ...

    def freeze(self, bullet, enemy):
        if self.meet(bullet, enemy) == 'Enemy':
            ...  # надо замедлять противника


class Weapon(pygame.sprite.Sprite):
    """
    оружия: 
    дальники: пистолет, шелли, байрон ...
    ближники: катана, топор, палка ...
    написаны в порядке убывания, типо катана самый мощный ближник и тп
    """

    def __init__(self, x, y, *groups):
        super().__init__(*groups)
        self.curr_mag_ammo: int = 0  # сколько патрон ща в магазе
        self.mag_capacity: int = 0  # сколько влазит в магаз
        self.ammo_max: int = 0  # сколько можно хранить патрон для этого оружия(без учета магаза)
        # (мб переделать типа патроны не индивидуально хранятся, а в инвентаре)
        self.all_ammo_current: int = 0  # скока ща всего патрон (без учета магаза)
        self.fire_rate: float = 0.0  # темп
        self.spread: float = 0.0  # разброс
        self.attack_sound: str = ''  # путь до звука
        self.name: str = 'NONE'
        self.rarity = None  # типа редкое\легендарное\эпичное и тп TODO: ДОБАВИТЬ РЕДКОСТЬ
        self.cooldown: float = 0.0  # кулдаун собсна В СЕКУНДАХ(через time делать потомучт буду)
        self.can_shoot: bool = True  # если нет патрон/перезарядка/кулдаун, то фолс
        self.frames = []
        self.cur_frame = 5
        self.cut_sheet(load_image("weapons/weapons1.png"), 10, 20)
        self.image = pygame.transform.scale(self.frames[self.cur_frame], (98, 44))

        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.pos = self.rect.topleft

    def cooldown_timer(self):
        self.can_shoot = False
        t_timer = Timer(self.cooldown, self.cooldown_finish)
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

    def shoot(self, user, mouse_pos):
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


class Gun(Weapon):
    """
        каркас стреляющего оружия
    """

    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups)
        self.curr_mag_ammo = 15
        self.no_ammo_sound: str = ''  # звук отсутствия патрон

    def shoot(self, user, mouse_pos):
        print('SHOOT')
        # current_time = pygame.time.get_ticks()  # а оно надо?
        if self.can_shoot and self.curr_mag_ammo > 0:
            self.curr_mag_ammo -= 1  # минус патрон
            direction = (mouse_pos[0] - user.pos[0], mouse_pos[1] - user.pos[1]) \
                if mouse_pos != user.pos else (1, 1)  # куда стреляем
            angle = math.radians(random.random() * self.spread - self.spread / 2)  # разброс случайны
            angled_direction = self.rotate_vector(direction, angle)  # траектория пули с учетом разброса

            # спавним пулю и передаем ей юзера, направление, скорость, длительность полета, цвет?(поменять на пнг)
            # и спрайт-группу
            Projectile(user.pos, super().normalize_vector(angled_direction), 15, 1000, (255, 0, 0), projectiles_group)
        if self.curr_mag_ammo == 0:
            print('NO AMMO')  # типа self.no_ammo_sound играть и мб как-то игроку показывать "NO AMMO"


class Melee(Weapon):
    """
    каркас оружия ближнего боя
    """

    def __init__(self, *groups):
        super().__init__(*groups)
        ...

# class SpreadGun(Weapon):
#     """
#     как шелли стреляет
#     """
#
#     def __init__(self):
#         super().__init__()
#         self.weapon_cooldown = 750
#         self.spread = 75
#         self.count_bullets = 7  # сколько пуль в разбросе
#
#     def shoot(self, user, mousePos, *groups):
#         super().__init__(*groups)
#         currentTime = pygame.time.get_ticks()
#         if self.curr_mag_ammo == 0:  # тип перезарядка
#             if currentTime - self.last_shot > self.cooldown:
#                 self.curr_mag_ammo = 100
#             else:
#                 return
#
#         self.curr_mag_ammo -= self.count_bullets  # минус патроны
#         if currentTime - self.last_shot > self.weapon_cooldown:
#             direction = (mousePos[0] - user.pos[0], mousePos[1] - user.pos[1]) \
#                 if mousePos != user.pos else (1, 1)
#             self.last_shot = currentTime
#             arcDifference = self.spread / (self.count_bullets - 1)
#             for proj in range(self.count_bullets):
#                 corner = math.radians(arcDifference * proj - self.spread / 2)
#                 projDir = super().rotate_vector(direction, corner)
#             # тут кароче надо как-то вызвать уже projectile
#             bullet = Projectile(user.pos, super().normalize_vector(projDir), 6, 1000, (255, 0, 0), projectiles_group)
#
#
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
