import ast
import os
import sys
from subprocess import Popen

import pygame
from pytmx import load_pygame

from menu import StartMenu
from network import Network
from trinkets import *
from weapon import *

# прикольно так накидал конечн

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

        self.pos: list = [x, y]  # левый верхний угол всегда
        self.prev_pos = self.pos

        self.health = 0
        self.alive = False
        self.movement_vector = [0, 0]
        self.movement_speed = 0
        self.look_at = 0, 0  # в эту точку повернут игрок головой
        self.available_weapons = []
        self.equipped_weapon = None
        self.inventory = []

        self.left_hand_slot = (0, 0)  # относительная позиция, считать от левого верхнего пикселя
        self.right_hand_slot = (0, 0)
        self.back_slot = (0, 0)

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
        if self in players_group and pygame.sprite.spritecollideany(self, weapons_group):
            for wep in weapons_group:
                if self.rect.colliderect(wep.rect):
                    print('PICKUPP')
                    wep.pick_up(self)

    def init_rect(self):
        self.rect = self.image.get_rect()
        self.rect.height = 5

    def update(self, *args):
        self.rect.topleft = self.pos

    def fire(self):
        pass  # стрелят

    def get_data(self):
        return {'POS': self.pos, 'HP': self.health, 'EQ_WEAPON': self.equipped_weapon}


class Player(Pawn):  # игрок
    image = pygame.transform.scale(load_image("templates/arrow.png"), (32, 32))

    # желательно без трансформа, просто сделать мелкий спрайт, но пока сойдет

    def __init__(self, x: int, y: int, nick: str, *groups):
        super().__init__(x, y, *groups)

        self.image = Player.image
        super(Player, self).init_rect()

        self.movement_speed = 5
        self.health = 100
        self.alive = True
        self.nick = nick
        self.available_weapons = []  # все оружия, TODO: добавить кулаки или другое стартовое
        self.equipped_weapon: int = 0  # это держим в руке, это индекс available_weapons. 0 <= i < len(av_weapons)
        self.inventory = []

        self.left_hand_slot = (15, 15)  # относительная позиция, считать от левого верхнего пикселя
        self.right_hand_slot = (60, 15)
        self.back_slot = (30, 0)

        self.multipliers = {'STRENGTH_P': 1, 'STRENGTH_M': 1}  # p плюс, m умножить потом перепишу
        self.trinkets = all_trinkets
        self.perks = []
        # с перками потом еще перепишу, а то чета отдельный список хранить в котором умножают отдельные
        # переменные, как-то неоч, тк есть еще и просто список перков(

    def move(self, server_player: list = False):
        super(Player, self).move()

        if server_player:
            self.pos = server_player
        else:
            k = pygame.key.get_pressed()
            m = pygame.mouse.get_pressed()
            if k[pygame.K_w]:
                self.movement_vector[1] += -1 * self.movement_speed
            if k[pygame.K_s]:
                self.movement_vector[1] += 1 * self.movement_speed
            if k[pygame.K_a]:
                self.movement_vector[0] += -1 * self.movement_speed
            if k[pygame.K_d]:
                self.movement_vector[0] += 1 * self.movement_speed
            if m[0]:  # лкм нажата
                self.shoot(pygame.mouse.get_pos())

        self.collision_test()

    def shoot(self, mouse_pos):  # стреляем
        if self.available_weapons:
            bul_data = self.available_weapons[self.equipped_weapon].shoot(self, mouse_pos)
            if bul_data:
                Projectile(*bul_data, projectiles_group)

    def update(self, *args):
        self.prev_pos = self.pos
        self.move()
        if self.available_weapons:  # TODO: ПЕРЕМЕЩАТЬ ВСЕ ОРУЖИЯ(ВСЕ СЛОТЫ ДВИГАТЬ)
            self.available_weapons[self.equipped_weapon].pos = \
                self.available_weapons[self.equipped_weapon].rect.topleft = \
                tuple(map(sum, zip(self.left_hand_slot, self.pos)))
        super(Player, self).update()

    def new_perk_add(self, perk):
        perk.use(self)

    def get_data(self):
        d = super().get_data()
        d['NICK'] = self.nick
        return d


class Enemy(Pawn):  # класс проутивников, от него наследоваться будут подклассы
    def __init__(self, x: int, y: int, *groups):
        super().__init__(x, y, *groups)
        self.movement_speed = 2
        self.health = 100
        self.alive = True
        super(Enemy, self).init_rect()

    def move(self):  # obj - объекты с которыми можем столкнуться
        super(Enemy, self).move()

        target = [(p, find_vector_len(self.pos, p.pos)) for p in players_group]  # берем живых игроков
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
        self.name = 'PLACEHOLDER'

        # скорость нужна чтобы предметы разлетались в разные стороны(например при смерти персонажа)
        self.movement_vector = [0, 0]
        self.movement_speed = 0

    def interact(self):
        pass


class Wall(pygame.sprite.Sprite):  # стены, от них наверн никого наследовать не надо
    image = pygame.transform.scale(load_image("templates/wall.jpg"), (32, 32))  # РАЗМЕР 1 ПЛИТКИ - 32х32

    def __init__(self, x, y, groups, rect_data, image=None):  # rect_data потом разберусь с ним, пока юзлес
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

    def __init__(self, source, target, speed, lifetime, *groups):
        # откуда, куда, скорость, сколько длится жизнь пули, цвет
        super().__init__(*groups)
        self.image = Projectile.bullet_image_default
        self.rect = self.image.get_rect()
        self.pos = [source[0], source[1]]
        self.movement_vector = [target[0], target[1]]
        self.speed = speed
        self.lifetime = lifetime
        self.when_created = pygame.time.get_ticks()

    def move(self, time):  # размер экрана и время
        if pygame.time.get_ticks() > self.when_created + self.lifetime:
            print('DIED')
            self.kill()  # пуля исчезает, если время ее жизни истекло
        self.pos[0] += self.movement_vector[0] * self.speed * time
        self.pos[1] += self.movement_vector[1] * self.speed * time
        self.rect.topleft = self.pos

    def update(self):
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


def find_vector_len(point_a, point_b):  # (x1,y1), (x2,y2)
    return ((point_a[0] - point_b[0]) ** 2 +
            (point_a[1] - point_b[1]) ** 2) ** 0.5


def game_loop():
    if mp_game:
        net = Network(ip_port)
    exit_condition = False
    finish_game = False

    players = {}  # содержит класс игрока по никам

    # спаун
    real_player = Player(430, 300, my_nickname, players_group)  # игрк
    Gun(460, 330, weapons_group)
    players[real_player.nick] = real_player
    for i in range(4):
        Wall(300 + 32 * i, 300, walls_group, [], None)
    for _ in range(6):
        Enemy(random.randint(0, screen.get_width()),
              random.randint(0, screen.get_height()), enemies_group)

    while not finish_game:  # игровой процесс, игра останавливается при условии finish_game == True
        if exit_condition:  # закрываем игру да
            return True

        # КАРОЧ ОТПРАВЛЯЮ ОТЕДЛЬНО СЛОВАРЬ ИГРОКОВ ОТДЕЛЬНО СЛОВАРЬ ВРАГОВ

        if mp_game:
            if im_a_host:  # если игрок хостит сервер - он и обрабатывает всю инфу
                # и посылает через сервер другим пепликсам
                to_send = [players[nick].get_data() for nick in players]
                reply = parse_data(send_data(net, 'HOST', to_send))  # отправляем на серв обработанную инфу
                # print('HOST', reply)
            else:  # игрок - клиент(подключился на чужой сервер)
                to_send = [
                    real_player.get_data()]  # сюда вписывать то, что отправляем на сервер: себя и все что с ним связано
                reply = parse_data(send_data(net, 'CLIENT', to_send))  # отправляем инфу и получаем ответ серва
                # print('USER', reply)
            try:  # обновляем инфу об игроках

                for p_nick in reply[0]:
                    if p_nick == real_player.nick:
                        continue
                    x, y = reply[0][p_nick]['POS']
                    if p_nick not in players:
                        players[p_nick] = Player(x, y, p_nick, players_group)  # другой игрк
                    players[p_nick].move([x, y])

            except Exception as e:
                print('MAIN//', e, reply)

        screen.fill(BGCOLOR)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_condition = True

        for p in players_group:
            p.update(screen)
        for e in enemies_group:
            e.update(screen)
        for bullet in projectiles_group:
            bullet.update()
        draw()  # рендерим тут

        pygame.display.flip()
        clock.tick(60)


def send_data(net, *data):
    global timeout
    reply = net.send(str(data))
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
        # print('server replied:', d)
        return d
    except Exception as e:
        print('PARSE//', e)
        return None


def draw():
    tile_group.draw(screen)

    all_sprites = [*players_group.sprites(), *enemies_group.sprites(), *deployable_group.sprites(),
                   *items_group.sprites(), *walls_group.sprites(), *weapons_group.sprites(),
                   *projectiles_group.sprites()]
    # ТУДА ВСЕ ГРУППЫ!!!(кроме tile_group)
    for spr in sorted(all_sprites, key=lambda x: x.pos[1]):  # сортируем по y и рендерим по убыванию
        screen.blit(spr.image, spr.rect)


def main():
    done = game_loop()
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.K_SPACE:  # TODO: сделать выход из гейм лупа сюда!
                game_loop()


def load_level(level_name):
    global game_map
    game_map = load_pygame(level_name)
    for layer in game_map.visible_layers:
        if layer.name == 'floor':
            for x, y, surf in layer.tiles():
                Tile(x * 32, y * 32, tile_group, surf)
        if layer.name == 'walls':
            for x, y, surf in layer.tiles():
                Wall(x * 32, y * 32, walls_group, [x * 32, y * 32, surf.get_width(), surf.get_height()], surf)


# группы снаружи if тк иначе они не импортнутся
projectiles_group = pygame.sprite.Group()
tile_group = pygame.sprite.Group()  # просто плитки, никакой коллизии/взаимодействия
players_group = pygame.sprite.Group()
enemies_group = pygame.sprite.Group()
deployable_group = pygame.sprite.Group()
items_group = pygame.sprite.Group()
walls_group = pygame.sprite.Group()
weapons_group = pygame.sprite.Group()

if __name__ == '__main__':  # ./venv/bin/python3 main.py ДЛЯ ЛИНУХА
    timeout = 0  # количество пустых ответов от сервера

    mp_game, im_a_host, my_nickname, ip_port = StartMenu(screen).run()
    print(mp_game, im_a_host, my_nickname, ip_port)

    # mp_game = True  # это сетевая или мультиплеер
    # im_a_host = True  # я хост или че
    # my_nickname = 'PLAYER 1'
    if im_a_host:
        SERVER = Popen([sys.executable, 'server.py'])  # парралельно с игрой запускаем сервер

    game_map = None  # просто чтоб было
    load_level("data/maps/dev_level.tmx")  # загружаем уровень после того как создали все спрайт-группы

    colliding = [enemies_group, walls_group, players_group]  # группы, которые имеют коллизию

    main()
