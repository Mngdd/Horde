import ast
import os
import sys
import time
from subprocess import Popen

import pygame
from pytmx import load_pygame
from menu import *
import random
from perks import *

from network import Network
from trinkets import *
from weapon import *

# прикольно так накидал конечн

DEBUG_START_SOLO = False
DEBUG_SPAWN_WEAPONS = False

enemy_spawn_event = pygame.USEREVENT + 1
wave_start_event = pygame.USEREVENT + 2

pygame.init()
size = (800, 600)
BGCOLOR = 'white'
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Top Down")
clock = pygame.time.Clock()


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


class Pawn(pygame.sprite.Sprite):
    image = pygame.transform.scale(load_image("templates/Obsolete.png"), (32, 32))

    def __init__(self, x: int, y: int, *groups):
        super().__init__(*groups)

        self.image = Pawn.image  # надо же чета вставить
        self.rect = self.image.get_rect()
        self.rect.height = 5  # чтоб за спрайт заходить можно было
        self.hitbox = self.image.get_rect()  # для коллизий, где нужна вся площадь (типа для монет)

        self.pos: list = [x, y]  # левый верхний угол всегда
        self.prev_pos = self.pos

        self.health = 0
        self.max_health = 100
        self.alive = False
        self.movement_vector = [0, 0]
        self.movement_speed = 0
        self.look_at = 0  # в эту точку повернут игрок головой
        self.available_weapons = []
        self.equipped_weapon = None
        self.inventory = []
        self.circle_mask = pygame.mask.from_surface(load_image("templates/circle.png"))
        self.damage_amount = 15  # ТОЛЬКО ДЛЯ ВРАГОВ

        self.left_hand_slot = (0, 0)  # относительная позиция, считать от левого верхнего пикселя
        self.right_hand_slot = (0, 0)
        self.back_slot = (0, 0)
        self.timing = time.time()
        self.damage_cooldown = 1  # ТОЛЬКО ДЛЯ ВРАГОВ

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        return [sheet.subsurface(pygame.Rect((self.rect.w * i, self.rect.h * j), self.rect.size))
                for j in range(rows) for i in range(columns)]

    def move(self):  # расчет передвижения
        self.pos[0] += self.movement_vector[0]
        self.pos[1] += self.movement_vector[1]
        self.movement_vector = [0, 0]

    def collision_test(self):  # коллизию считаем
        test_rect_no_x = self.rect.copy()
        test_rect_no_x.topleft = (self.pos[0], self.pos[1] + self.movement_vector[1])
        test_rect_no_y = self.rect.copy()
        test_rect_no_y.topleft = (self.pos[0] + self.movement_vector[0], self.pos[1])

        for group in colliding:  # обрабатываем столкновения со всеми объектами
            for el in group:
                if self in enemies_group and el in players_group and el.alive:
                    if pygame.sprite.collide_mask(self, el) and time.time() - self.timing > self.damage_cooldown:
                        self.timing = time.time()
                        random.choice(self.hit_sounds).play()
                        el.damage(random.randint(*self.damage_amount))  # враг всем в радиусе урон наносит

                if el == self or (self in players_group and (el in players_group or el in enemies_group)) or \
                        (self in enemies_group and el in players_group):
                    # игроки не сталкиваются друг с другом (и с врагами тож)
                    continue
                if test_rect_no_x.colliderect(el.rect):  # столкновение по у в будущей позиции, туда не идем
                    self.movement_vector[1] = 0
                if test_rect_no_y.colliderect(el.rect):  # столкновение по х в будущей позиции, туда не идем
                    self.movement_vector[0] = 0
                if self.rect.colliderect(el.rect):  # НЕ ДОПУСКАТЬ ЗАСТРЯВАНИЕ ВООБЩЕ!!!, но если застряли,
                    # то перемещаем в предыдущую позицию
                    self.pos = self.prev_pos  # это не сработает если в предыдущей позиции мы уже застряли
                    # если такое будет происходить, я попробую еще чета, но пока сойдет

    def init_rect(self):
        self.rect = self.image.get_rect()
        self.rect.height = 5

    def update(self, *args):
        self.rect.topleft = self.pos
        self.hitbox.topleft = self.pos
        if self.available_weapons:
            wep, m_pos = self.available_weapons[self.equipped_weapon], pygame.mouse.get_pos()
            # wep.angle = 180 - math.degrees(math.atan2(m_pos[1] - wep.pos[1], m_pos[0] - wep.pos[0]))

    def get_data(self):
        return {'POS': self.pos, 'HP': self.health, 'EQ_WEAPON': self.equipped_weapon}

    def damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.alive = False
        if self in enemies_group:
            self.kill()
            Coin(self.hitbox.center, coins_group)

    def draw_health_bar(self, screen: pygame.Surface, camera_pos: pygame.math.Vector2):
        # для оптимизации можно рисовать это в self.image и перерисовывать, когда меняется здоровье,
        # но тогда придется копировать картинку для каждого
        height = 5
        y = self.rect.y + 32 - height - camera_pos.y
        width = round(32 * self.health / self.max_health)
        pygame.draw.rect(screen, (0, 0, 0), pygame.rect.Rect(self.rect.x - camera_pos.x, y, self.rect.width, height))  # черная часть
        pygame.draw.rect(screen, (255, 0, 0), pygame.rect.Rect(self.rect.x - camera_pos.x, y, width, height))  # красная часть


class Player(Pawn):  # игрок
    image = pygame.transform.scale(load_image("templates/arrow.png"), (32, 32))

    # желательно без трансформа, просто сделать мелкий спрайт, но пока сойдет

    def __init__(self, x: int, y: int, nick: str, *groups):
        super().__init__(x, y, *groups)

        self.states = {'IDLE': self.cut_sheet(load_image("characters/skeleton/skeleton_idle.png"), 4, 4),
                       'WALK': self.cut_sheet(load_image('characters/skeleton/skeleton_walk.png'), 4, 4),
                       'HURT': self.cut_sheet(load_image('characters/skeleton/skeleton_hurt.png'), 2, 4),
                       'DEATH': self.cut_sheet(load_image('characters/skeleton/skeleton_death.png'), 4, 4)}

        self.movement_speed = 5
        self.health = 100
        self.max_health = 100
        self.alive = True
        self.curr_state = 'IDLE'
        self.nick = nick
        self.action_text = ''  # по центру текст тип перезарядка или еще чет
        self.available_weapons = []  # все оружия, TODO: добавить кулаки или другое стартовое
        self.equipped_weapon: int = 0  # это держим в руке, это индекс available_weapons. 0 <= i < len(av_weapons)
        self.inventory = []
        self.money = 10  # чтоб достаточно для минимального оружия

        self.left_hand_slot = (0, 5)  # относительная позиция, считать от левого верхнего пикселя
        self.right_hand_slot = (10, 5)
        self.back_slot = (5, 0)

        self.multipliers = {'STRENGTH_P': 1, 'STRENGTH_M': 1}  # p плюс, m умножить потом перепишу
        self.trinkets = all_trinkets
        self.perks = []

        self.cur_frame = 0  # номер кадра с картинкой оружия
        self.image = pygame.transform.scale(self.states[self.curr_state][self.cur_frame], (72, 72))

        super(Player, self).init_rect()
        self.move_frame()
        # с перками потом еще перепишу, а то чета отдельный список хранить в котором умножают отдельные
        # переменные, как-то неоч, тк есть еще и просто список перков(

        self.overlay_open = False  # для магаза, меню паузы может

    def get_player_looking_angle(self):
        vec_pos = pygame.math.Vector2(self.pos - camera_pos)
        direction = pygame.mouse.get_pos() - vec_pos
        radius, angle = direction.as_polar()
        return angle

    def move(self, server_player: list = False):
        super(Player, self).move()

        if server_player:
            self.pos = server_player
        else:
            k = pygame.key.get_pressed()
            m = pygame.mouse.get_pressed()
            self.curr_state = 'IDLE'
            # TODO: ПЕРЕДЕЛАТЬ РАЗВОРОТ БАШКИ ПОД ПОЗИЦИЮ МЫШКИ
            angle = self.get_player_looking_angle()
            if -135 > angle > -180 or 135 <= angle <= 180:  # налево
                self.look_at = 1  # 0-вниз 1-налево 2-направо 3-наверх
            elif 45 <= angle <= 135:  # вниз
                self.look_at = 0
            elif 45 > angle > 0 or -45 <= angle <= 0:  # направо
                self.look_at = 2
            elif -45 >= angle >= -135:  # наверх
                self.look_at = 3

            if k[pygame.K_w]:
                self.movement_vector[1] += -1 * self.movement_speed
                self.curr_state = 'WALK'
            if k[pygame.K_s]:
                self.movement_vector[1] += 1 * self.movement_speed
                self.curr_state = 'WALK'
            if k[pygame.K_a]:
                self.movement_vector[0] += -1 * self.movement_speed
                self.curr_state = 'WALK'
            if k[pygame.K_d]:
                self.movement_vector[0] += 1 * self.movement_speed
                self.curr_state = 'WALK'
            if k[pygame.K_r]:
                if self.available_weapons and not self.available_weapons[self.equipped_weapon].reloading:
                    self.available_weapons[self.equipped_weapon].reload()
            if k[pygame.K_q]:
                if self.equipped_weapon != -1 and self.available_weapons:
                    self.force_drop_weapon()

            if m[0]:  # лкм нажата
                self.shoot(pygame.mouse.get_pos())

        if pygame.sprite.spritecollideany(self, weapons_group):
            for wep in weapons_group:
                if self.rect.colliderect(wep.rect):
                    if k[pygame.K_e]:
                        self.pickup_weapon(wep)
                    else:
                        self.action_text = f'PICK UP {wep.name}'

        self.collision_test()

    def pickup_weapon(self, weapon):
        if self.equipped_weapon != -1 and self.available_weapons:
            self.available_weapons.pop(-1)
            self.equipped_weapon = -1
        weapon.pick_up(self)

    def force_drop_weapon(self):
        print('dropped weapon',  self.available_weapons, self.equipped_weapon)
        self.available_weapons.pop(-1)
        self.equipped_weapon = -1

    def pick_up_coins(self):
        for coin in coins_group:
            if self.hitbox.collidepoint(*coin.pos):
                coin.kill()
                self.money += 1

    def close_shop(self):
        global shop
        shop.close_overlay()
        self.overlay_open = False

    def check_shop(self):
        global shop
        if pygame.key.get_pressed()[pygame.K_e] and not self.overlay_open:
            if shop.can_access(self):
                shop.open_overlay()
                self.overlay_open = True
        if pygame.key.get_pressed()[pygame.K_ESCAPE] and self.overlay_open:
            self.close_shop()

    def move_frame(self):
        self.timing = time.time()
        self.cur_frame = self.cur_frame + 1 if self.cur_frame < 3 else 0

    def shoot(self, mouse_pos):  # стреляем
        if self.available_weapons and self.available_weapons[self.equipped_weapon].can_shoot:
            bul_data = self.available_weapons[self.equipped_weapon].shoot(self, mouse_pos, camera_pos)
            if bul_data:
                if self.available_weapons[self.equipped_weapon].shoot_type == Weapon.SHOTGUN:
                    for i in range(len(bul_data)):
                        bul_data[i][0][0] += self.right_hand_slot[0]
                        bul_data[i][0][1] += self.right_hand_slot[1]
                        Projectile(*bul_data[i], enemies_group, projectiles_group)
                else:
                    bul_data[0][0] += self.right_hand_slot[0]
                    bul_data[0][1] += self.right_hand_slot[1]
                    Projectile(*bul_data, enemies_group, projectiles_group)

    def update(self, *args):
        if self.alive:
            self.action_text = ''
            if time.time() - self.timing > 0.35:
                self.move_frame()
            self.image = pygame.transform.scale(self.states[self.curr_state][self.cur_frame + self.look_at * 4], (72, 72))
            if self.available_weapons and self.available_weapons[self.equipped_weapon].reloading:
                self.action_text = f'RELOADING...'
            if not self.overlay_open:
                self.prev_pos = self.pos
                self.move()
            self.check_shop()
            self.pick_up_coins()
            if self.available_weapons:  # TODO: ПЕРЕМЕЩАТЬ ВСЕ ОРУЖИЯ(ВСЕ СЛОТЫ ДВИГАТЬ)
                self.available_weapons[self.equipped_weapon].pos = \
                    self.available_weapons[self.equipped_weapon].rect.topleft = \
                    tuple(map(sum, zip(self.left_hand_slot, self.pos)))
                ang = int(self.get_player_looking_angle())
                self.available_weapons[self.equipped_weapon].angle = 180 - ang
            super(Player, self).update()
        else:
            self.action_text = 'DEAD'

    def new_perk_add(self, perk):
        perk.use(self)

    def get_data(self):
        d = super().get_data()
        d['NICK'] = self.nick
        return d


class Enemy(Pawn):  # класс проутивников, от него наследоваться будут подклассы
    def __init__(self, x: int, y: int, *groups):
        super().__init__(x, y, *groups)
        self.movement_speed = round(random.uniform(1.0, 3.0), 1)
        self.health = 100
        self.max_health = 100
        self.damage_amount = (5, 15)
        self.alive = True
        self.damage_cooldown = 0.5
        self.available_weapons = []
        self.equipped_weapon = -1
        self.hit_sounds = [Weapon.load_sound(Melee, f'melee_hit{i}.mp3', 0.5) for i in range(1, 4)]
        super(Enemy, self).init_rect()

    def move(self):  # obj - объекты с которыми можем столкнуться
        super(Enemy, self).move()

        target = [(p, find_vector_len(self.pos, p.pos)) for p in players_group if p.alive]  # берем живых игроков
        if target:
            target = sorted(target, key=lambda x: (x[1], x[0].health, x[0].nick))[0][0]  # кого бьем
            if target.pos[1] < self.pos[1]:
                self.movement_vector[1] += -1 * self.movement_speed  # вверх
            if target.pos[1] > self.pos[1]:
                self.movement_vector[1] += 1 * self.movement_speed  # вниз
            if target.pos[0] < self.pos[0]:
                self.movement_vector[0] += -1 * self.movement_speed  # налево
            if target.pos[0] > self.pos[0]:
                self.movement_vector[0] += 1 * self.movement_speed  # направо

            self.collision_test()

    def update(self, *args):
        self.prev_pos = self.pos
        self.move()
        super(Enemy, self).update()

    def get_data(self):
        return {'TYPE': 'E', 'POS': self.pos, 'HP': self.health, 'SPEED': self.movement_speed}


class Deployable(Pawn):  # гаджетиы - турели/мины и всякое такое что пассивно наносит урон врагам
    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups)
        self.image.fill('cyan')
    # TODO: сделать


class Item(pygame.sprite.Sprite):  # предметы лежащие на земле, можно подбирать их
    def __init__(self, x, y, *groups):
        super().__init__(*groups)
        self.image = Pawn.image  # тк это базовый класс, его не должно быть в игре
        self.rect = self.image.get_rect()
        self.pos = [x, y]
        self.rect.topleft = self.pos
        self.name = 'PLACEHOLDER'

        # скорость нужна чтобы предметы разлетались в разные стороны(например при смерти персонажа)
        self.movement_vector = [0, 0]
        self.movement_speed = 0

    def interact(self):
        pass


class Wall(pygame.sprite.Sprite):  # стены, от них наверн никого наследовать не надо
    image = pygame.transform.scale(load_image("templates/wall.jpg"), (32, 32))  # РАЗМЕР 1 ПЛИТКИ - 32х32

    def __init__(self, x, y, groups, rect_data, image=None):  # TODO: в rect_data загружать инфу о коллизии(точки)
        super().__init__(groups)
        self.pos = [x, y]
        self.image = Wall.image if image is None else image

        self.rect = self.image.get_rect()
        self.rect.height = 5
        self.rect.topleft = self.pos


class Tile(pygame.sprite.Sprite):  # просто плитки, никакой коллизии
    image = pygame.transform.scale(load_image("templates/grass.jpg"), (32, 32))  # РАЗМЕР 1 ПЛИТКИ - 32х32

    def __init__(self, x, y, groups, image=None):
        super().__init__(groups)
        self.pos = [x, y]
        self.image = Tile.image if image is None else image
        self.rect = self.image.get_rect()
        self.rect.topleft = self.pos


class Projectile(pygame.sprite.Sprite):  # пуля сама
    bullet_image_default = pygame.transform.scale(load_image("weapons/bullet1.png"), (8, 8))

    def __init__(self, source, target, speed, lifetime, damage, enemy_team, *groups, bid=None):
        global b_id_counter
        # откуда, куда, скорость, сколько длится жизнь пули, цвет
        super().__init__(*groups)
        self.image = Projectile.bullet_image_default
        self.rect = self.image.get_rect()
        self.pos = [source[0], source[1]]
        self.movement_vector = [target[0], target[1]]
        self.speed = speed
        self.lifetime = lifetime
        self.when_created = pygame.time.get_ticks()
        self.damage = damage
        self.enemy_team = enemy_team
        if bid is None:
            self.id = b_id_counter  # мега костыль чтобы избежать повтора пуль
            b_ids.append(self.id)
            b_id_counter += 1
        else:
            self.id = bid

    def move(self, time):  # размер экрана и время
        if pygame.time.get_ticks() > self.when_created + self.lifetime:
            self.kill()  # пуля исчезает, если время ее жизни истекло
        self.pos[0] += self.movement_vector[0] * self.speed * time
        self.pos[1] += self.movement_vector[1] * self.speed * time
        self.rect.topleft = self.pos

    def update(self):
        self.move(2)
        if pygame.sprite.spritecollideany(self, walls_group):
            self.kill()
        for el in self.enemy_team:
            if self.rect.colliderect(el.rect):  # столкновение по у в будущей позиции, туда не идем
                el.damage(self.damage)
                self.kill()

    def render(self, surface):
        surface.blit(self.image, self.pos)

    def meet(self, bullet, obj) -> str:
        if pygame.sprite.spritecollide(bullet, obj, False, pygame.sprite.collide_rect):
            return obj.__name__

    def hit(self, bullet, enemy):
        ...

    def freeze(self, bullet, enemy):
        if self.meet(bullet, enemy) == 'Enemy':
            ...  # надо замедлять противника

    def get_data(self):
        return {'TYPE': 'B', 'POS': self.pos, 'DMG': self.damage, 'TARG': self.movement_vector,
                'TIME':self.lifetime, 'ID': self.id}


class Coin(pygame.sprite.Sprite):
    image = load_image("templates/catacombs/candleA_01.png")

    def __init__(self, point: tuple[int, int], *groups):
        super().__init__(*groups)
        self.pos = point  # коллизия по точкам, чтобы не сильно нагружать
        self.image = Coin.image
        self.rect = self.image.get_rect()
        self.rect.center = self.pos


class ScreenDarken(WidgetBase):
    def __init__(self):
        super(ScreenDarken, self).__init__(screen, 0, 0, size[0], size[1])
        self.rect = pygame.rect.Rect(0, 0, size[0], size[1])
        self.surf = pygame.surface.Surface(size).convert_alpha()
        pygame.draw.rect(self.surf, (0, 0, 0, 127), self.rect)
        self.hidden = False

    def draw(self):
        if not self.hidden:
            self.win.blit(self.surf, (0, 0))

    def listen(self, events):
        pass

    def hide(self):
        self.hidden = True

    def show(self):
        self.hidden = False


class Shop(pygame.sprite.Sprite):  # от спрайта наследование чтобы когда камера будет работало
    def __init__(self, x: int, y: int, closed: bool = True):
        super(Shop, self).__init__()
        self.rect = pygame.rect.Rect(x - 32, y - 32, 32 * 3, 32 * 3)  # область 3x3 тайла вокруг
        self.overlay_widgets = [ScreenDarken()]
        for i, weapon_class in enumerate(purchasable_weapons, 1):
            weapon = weapon_class(-2000, -2000)  # чтобы прочитать атрибуты
            x = 250
            width = size[0] - x * 2
            label_width = 50
            height = 48
            y = i * (height + 10)
            new_btn = Button(screen, x, y, width - label_width, height, text=weapon.name, image=weapon.image,
                             textHAlign='left', imageHAlign='right', onClick=self.buy(weapon_class, weapon.price),
                             font=pygame.font.SysFont('Cascadia Code', 30))
            new_label = Label(screen, x + width - label_width, y, label_width, height, text=str(weapon.price),
                              textColour='grey', font=pygame.font.SysFont('Cascadia Code', 30))
            self.overlay_widgets.append(new_btn)
            self.overlay_widgets.append(new_label)
            weapon.kill()
        if closed:
            self.close_overlay()

    @staticmethod
    def buy(weapon_class, price: int):
        def inner():
            global real_player
            if real_player.money < price:
                return
            real_player.money -= price
            weapon = weapon_class(*real_player.pos, weapons_group)
            real_player.pickup_weapon(weapon)
        return inner

    def can_access(self, player: Player):
        return player.rect.colliderect(self.rect)

    def open_overlay(self):
        print('открыт магаз')
        for widget in self.overlay_widgets:
            widget.show()

    def close_overlay(self):
        print('закрыт магаз')
        for widget in self.overlay_widgets:
            widget.hide()


def find_vector_len(point_a, point_b):  # (x1,y1), (x2,y2)
    return ((point_a[0] - point_b[0]) ** 2 +
            (point_a[1] - point_b[1]) ** 2) ** 0.5


def game_loop():
    global real_player, camera_pos
    if mp_game:
        net = Network(ip_port)
    exit_condition = False
    finish_game = False

    half_x, half_y = screen.get_width() // 2, screen.get_height() // 2  # для камеры

    players = {}  # содержит класс игрока по никам

    # спаун
    real_player = Player(430, 300, my_nickname, players_group)  # игрк
    if DEBUG_SPAWN_WEAPONS:
        Usp(520, 250, weapons_group)
        Spas12(520, 300, weapons_group)
        M16(520, 350, weapons_group)
        AK47(520, 400, weapons_group)
        Minigun(520, 450, weapons_group)
        Awp(520, 500, weapons_group)
    players[real_player.nick] = real_player
    for i in range(4):
        Wall(300 + 32 * i, 300, walls_group, [], None)

    waves = [2, 6, 14]  # кол-ва противников в волнах
    pause_duration = 20000  # время между волнами
    next_wave_time = time.time() + pause_duration / 1000
    spawn_rate = 3500  # время между спавнами
    wave_index = 0
    wave_ongoing = False  # идет ли волна. если False, то перерыв
    enemies_to_spawn = 0  # сколько врагов еще заспавнить (из всех спавнпоинтов за 1 раз)

    pygame.time.set_timer(wave_start_event, pause_duration, 1)  # через pause_duration начнется волна
    pygame.time.set_timer(enemy_spawn_event, spawn_rate)  # ивент срабатывает постоянно, но спавн при enemies_to_spawn > 0

    while not finish_game:  # игровой процесс, игра останавливается при условии finish_game == True
        if exit_condition:  # закрываем игру да
            return True

        # КАРОЧ ОТПРАВЛЯЮ ОТЕДЛЬНО СЛОВАРЬ ИГРОКОВ ОТДЕЛЬНО СЛОВАРЬ ВРАГОВ

        if mp_game:
            if im_a_host:  # если игрок хостит сервер - он и обрабатывает всю инфу
                # и посылает через сервер другим пепликсам
                to_send = [players[nick].get_data() for nick in players]
                to_send.extend([b.get_data() for b in projectiles_group])
                to_send.extend([e.get_data() for e in enemies_group])
                reply = parse_data(send_data(net, 'HOST', to_send))  # отправляем на серв обработанную инфу
                # print('HOST', reply)
            else:  # игрок - клиент(подключился на чужой сервер)
                to_send = [real_player.get_data()]  # сюда вписывать то, что отправляем на сервер:
                # себя и все что с ним связано
                to_send.extend([b.get_data() for b in projectiles_group])
                reply = parse_data(send_data(net, 'CLIENT', to_send))  # отправляем инфу и получаем ответ серва
            try:  # обновляем инфу об игроках
                for p_nick in reply[0]:
                    # print('\t', reply)
                    if p_nick == real_player.nick:
                        continue
                    x, y = reply[0][p_nick]['POS']
                    if p_nick not in players:
                        players[p_nick] = Player(x, y, p_nick, players_group)  # другой игрк
                    players[p_nick].move([x, y])
                for bul_data in reply[2]:
                    print('\t', bul_data)
                    if bul_data['ID'] not in b_ids:
                        Projectile(bul_data['POS'], bul_data['TARG'], 5, bul_data['TIME'], bul_data['DMG'], enemies_group,
                                   projectiles_group, bid=bul_data['ID'])

            except Exception as e:
                print('MAIN//', e, reply)

        screen.fill(BGCOLOR)

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                exit_condition = True
            elif event.type == enemy_spawn_event and enemies_to_spawn > 0:  # спавн противников
                for x, y in enemy_spawnpoints:
                    Enemy(x, y, enemies_group)
                enemies_to_spawn -= 1
            elif event.type == wave_start_event:  # начало волны
                enemies_to_spawn = waves[wave_index]
                wave_ongoing = True

        if len(enemies_group) == 0 and enemies_to_spawn <= 0 and wave_ongoing:  # конец волны
            pygame.time.set_timer(wave_start_event, pause_duration, 1)
            next_wave_time = time.time() + pause_duration / 1000
            wave_index += 1
            if wave_index >= len(waves):
                finish_game = True
            wave_ongoing = False

        for p in players_group:
            p.update(screen)
        for e in enemies_group:
            e.update(screen)
        for bullet in projectiles_group:
            bullet.update()

        camera_pos.x = real_player.rect.centerx - half_x  # тащим камеру
        camera_pos.y = real_player.rect.centery - half_y

        draw()  # рендерим тут
        if not wave_ongoing:
            screen.blit(font.render(f'UNTIL START OF WAVE: {int(next_wave_time - time.time())}', True, (15, 15, 15)), get_screen_cords(5, 5))
        screen.blit(font.render(f'WAVE {wave_index + 1}/{len(waves)}', True, (15, 15, 15)), get_screen_cords(85, 5))
        pygame_widgets.update(events)  # чтобы интерфейс поверх всего рисовался

        pygame.display.flip()
        clock.tick(60)
    EndMenu(screen, real_player.money).run()


def send_data(net, *data):
    global timeout
    reply = net.send(str(data))
    # print('server replied:', reply)
    if reply == '':  # можна канеш сразу при пустом ответе помирать, но на всякий я так сделаю
        timeout += 1
    else:
        timeout = 0

    if timeout >= 10:
        raise Exception('ОТВЕТА НЕТ. ОТКЛЮЧЕН')
    return reply


def parse_data(data):
    try:
        d = ast.literal_eval(data)
        return d
    except Exception as e:
        print('PARSE//', e)
        exit(-1)  # TODO: убрать потом


def draw():
    for t in tile_group:
        screen.blit(t.image, t.rect.topleft - camera_pos)
    all_sprites = [*players_group.sprites(), *enemies_group.sprites(), *deployable_group.sprites(),
                   *items_group.sprites(), *walls_group.sprites(), *coins_group.sprites(), *weapons_group.sprites(),
                   *projectiles_group.sprites()]
    # ТУДА ВСЕ ГРУППЫ!!!(кроме tile_group)
    for spr in sorted(all_sprites, key=lambda x: x.pos[1]):  # сортируем по y и рендерим по убыванию
        if spr in weapons_group:  # тут не только веапоны, а все что вращается, но пока что это веапоны только
            if 270 >= spr.angle >= 90:
                transformed_img = pygame.transform.rotate(spr.image, -spr.angle)
                transformed_img = pygame.transform.flip(transformed_img, False, True)
            else:
                transformed_img = pygame.transform.rotate(spr.image, spr.angle)

            screen.blit(transformed_img, spr.rect.topleft - camera_pos)
        elif spr in players_group:
            new_rect = spr.image.get_rect(center=spr.image.get_rect(topleft=spr.rect.topleft).center)
            new_rect.topleft = [new_rect.topleft[0] - camera_pos.x, new_rect.topleft[1] - 25 - camera_pos.y]
            screen.blit(spr.image, new_rect.topleft)
        else:
            screen.blit(spr.image, spr.rect.topleft - camera_pos)
            if isinstance(spr, Pawn):  # для игрока не рисуем, т.к. баг (шкала слишком широкая)
                spr.draw_health_bar(screen, camera_pos)

    # рисуем HUD
    curr = real_player.available_weapons[real_player.equipped_weapon].curr_mag_ammo \
        if real_player.available_weapons else 0
    total = real_player.available_weapons[real_player.equipped_weapon].all_ammo_current \
        if real_player.available_weapons else 0
    wep_name = real_player.available_weapons[real_player.equipped_weapon].name \
        if real_player.available_weapons else 'Nothing'
    # + hud для волн рисуется в game_loop, т.к. там все переменные для этого
    screen.blit(font.render(f'CANDLES: {real_player.money}', True, (15, 15, 15)), get_screen_cords(5, 85))
    screen.blit(font.render(f'HP: {real_player.health}', True, (15, 15, 15)), get_screen_cords(5, 90))
    screen.blit(font.render(f'{wep_name}  {curr}/{total}', True, (15, 15, 15)), get_screen_cords(75, 90))
    screen.blit(font.render(f'{real_player.action_text}', True, (15, 15, 15)), get_screen_cords(35, 90))


def get_screen_cords(x, y):  # проценты от экрана
    return screen.get_width() // 100 * x, screen.get_height() // 100 * y


def main():
    done = game_loop()
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.K_SPACE:  # TODO: сделать выход из гейм лупа сюда!
                game_loop()


def load_level(level_name):
    global game_map, shop, enemy_spawnpoints
    game_map = load_pygame(level_name)
    for layer_number, layer in enumerate(game_map.visible_layers):
        if layer.name == 'floor':
            for x, y, surf in layer.tiles():
                Tile(x * 32, y * 32, tile_group, surf)
        if layer.name == 'walls':
            for x, y, surf in layer.tiles():
                Wall(x * 32, y * 32, walls_group, [x * 32, y * 32, surf.get_width(), surf.get_height()], surf)
    for object_group in game_map.objectgroups:
        if object_group.name == 'enemy_spawnpoints':
            enemy_spawnpoints = [(point.x, point.y) for point in object_group]
        elif object_group.name == 'shops':
            for point in object_group:
                shop = Shop(point.x, point.y)
                break
    assert enemy_spawnpoints, 'нет спавнпоинтов'
    assert shop, 'нет магазина'


# группы снаружи if тк иначе они не импортнутся
projectiles_group = pygame.sprite.Group()
tile_group = pygame.sprite.Group()  # просто плитки, никакой коллизии/взаимодействия
players_group = pygame.sprite.Group()
enemies_group = pygame.sprite.Group()
deployable_group = pygame.sprite.Group()
items_group = pygame.sprite.Group()
walls_group = pygame.sprite.Group()
weapons_group = pygame.sprite.Group()
coins_group = pygame.sprite.Group()
font = pygame.font.SysFont('Cascadia Code', 30)

b_ids = []
b_id_counter = 0
camera_pos = pygame.math.Vector2(100, 100)
if __name__ == '__main__':  # ./venv/bin/python3 main.py ДЛЯ ЛИНУХА
    timeout = 0  # количество пустых ответов от сервера

    if not DEBUG_START_SOLO:
        mp_game, im_a_host, my_nickname, ip_port, level_file = StartMenu(screen).run()
    else:
        mp_game, im_a_host, my_nickname, ip_port, level_file = False, False, 'debug', None, 'dev_level.tmx'
    print(mp_game, im_a_host, my_nickname, ip_port, level_file)

    # mp_game = True  # это сетевая или мультиплеер
    # im_a_host = True  # я хост или че
    # my_nickname = 'PLAYER 1'
    if im_a_host:
        SERVER = Popen([sys.executable, 'server.py'])  # парралельно с игрой запускаем сервер

    shop: Shop = None
    game_map = None  # просто чтоб было
    enemy_spawnpoints = None
    print(os.path.join("data/maps/", level_file))
    load_level(os.path.join("data/maps/", level_file))  # загружаем уровень после того как создали все спрайт-группы

    colliding = [enemies_group, walls_group, players_group]  # группы, которые имеют коллизию

    main()
