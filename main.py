import os
import sys
from network import Network
import pygame
from pytmx import load_pygame
from menu import StartMenu
import ast
import random

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

        self.pos = [x, y]  # левый верхний угол всегда
        self.health = 0
        self.alive = False
        self.movement_vector = [0, 0]
        self.movement_speed = 0
        self.look_at = 0, 0  # в эту точку повернут игрок головой
        self.available_weapons = []
        self.equipped_weapon = None
        self.inventory = []
        self.prev_pos = self.pos

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

    def init_rect(self):
        self.rect = self.image.get_rect()
        self.rect.height = 5

    def update(self, *args):
        self.rect.topleft = self.pos

    def fire(self):
        pass  # стрелят


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
        # TODO: нужно оружие
        self.available_weapons = []
        self.equipped_weapon = None
        self.inventory = []

    def move(self, server_player=False):
        super(Player, self).move()

        if server_player:
            self.movement_vector[1] = server_player[1]
            self.movement_vector[0] = server_player[0]
        else:
            k = pygame.key.get_pressed()
            if k[pygame.K_w]:
                self.movement_vector[1] += -1 * self.movement_speed
            if k[pygame.K_s]:
                self.movement_vector[1] += 1 * self.movement_speed
            if k[pygame.K_a]:
                self.movement_vector[0] += -1 * self.movement_speed
            if k[pygame.K_d]:
                self.movement_vector[0] += 1 * self.movement_speed

        self.collision_test()

    def update(self, *args):
        self.prev_pos = self.pos
        self.move()
        super(Player, self).update()


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


class Weapon(pygame.sprite.Sprite):
    def __init__(self, *groups):
        super().__init__(*groups)
        self.curr_mag_ammo = 0  # сколько патрон ща в магазе
        self.mag_capacity = 0  # сколько влазит в магаз
        self.ammo_max = 0  # сколько можно хранить патрон для этого оружия(без учета магаза)
        # (мб переделать типа патроны не индивидуально хранятся, а в инвентаре)
        self.all_ammo_current = 0  # скока ща всего патрон (без учета магаза)
        self.firerate = 0.0  # темп
        self.spread = 0.0  # разброс
        self.name = 'NONE'
        self.rarity = None  # типа редкое\легендарное\эпичное и тп

    def shoot(self):
        pass

    def reload(self):
        pass


class Projectile(pygame.sprite.Sprite):  # пуля сама
    def __init__(self, *groups):
        super().__init__(*groups)


def find_vector_len(point_a, point_b):  # (x1,y1), (x2,y2)
    return ((point_a[0] - point_b[0]) ** 2 +
            (point_a[1] - point_b[1]) ** 2) ** 0.5


def game_loop():
    if mp_game:
        net = Network()
    exit_condition = False
    finish_game = False

    players = {}  # {'test': {'online': False, 'ip': -1, 'vars': [None]}}  # такой же как и в сервер пай
    # спаун
    p = Player(430, 300, 'JOHN CENA', players_group)  # игрк

    for i in range(4):
        Wall(300 + 32 * i, 300, walls_group, [], None)
    for _ in range(6):
        Enemy(random.randint(0, screen.get_width()),
              random.randint(0, screen.get_height()), enemies_group)

    while not finish_game:  # игровой процесс, игра останавливается при условии finish_game == True
        if exit_condition:  # закрываем игру да
            return True

        # TODO: ПОЛУЧАТЬ ВРАГОВ ТОЖЕ И ПОЧИНИТЬ МЕНЯ!!!!!!!!!

        if mp_game:
            players_list = parse_data(send_data([p.nick, p.pos], net))  # пока отправляем только корды игркв
            print(players_list)
            try:
                for player_nick in players_list:
                    x, y = players_list[player_nick]
                    if players_list[player_nick] not in players:
                        players[player_nick] = Player(x, y, player_nick, players_group)  # другой игрк
                    players[player_nick].move((x, y))

                    # players_list[player_data[0]] = player_data[1]
                    # print(players_list, players)
            except Exception as e:
                print('MAIN//', e)

        screen.fill(BGCOLOR)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_condition = True

        for p in players_group:
            p.update(screen)
        for e in enemies_group:
            e.update(screen)

        draw()  # рендерим тут

        pygame.display.flip()
        clock.tick(75)


def send_data(data, net):  # TODO: ПОМЕНЯТЬ ОТПРАВЛЯЕМУЮ И ПОЛУЧАЕМУЮ ИНФОРМАЦИЮ
    """
    Send position to server
    :return: None
    """
    reply = net.send(str(data))
    return reply


def parse_data(data):
    try:
        d = ast.literal_eval(data)  # TODO: тут тоже доделать
        return d
    except Exception as e:
        print('PARSE//', e)
        return None


def draw():
    tile_group.draw(screen)

    all_sprites = [*players_group.sprites(), *enemies_group.sprites(), *deployable_group.sprites(),
                   *items_group.sprites(), *walls_group.sprites()]
    # ТУДА ВСЕ ГРУППЫ!!!(кроме tile_group)
    for spr in sorted(all_sprites, key=lambda x: x.pos[1]):  # сортируем по y и рендерим по убыванию
        screen.blit(spr.image, spr.rect)


def main():
    action = StartMenu(screen).run()
    if action == StartMenu.PLAY:
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


if __name__ == '__main__':
    mp_game = True  # это сетевая или мультиплеер

    tile_group = pygame.sprite.Group()  # просто плитки, никакой коллизии/взаимодействия
    players_group = pygame.sprite.Group()
    enemies_group = pygame.sprite.Group()
    deployable_group = pygame.sprite.Group()
    items_group = pygame.sprite.Group()
    walls_group = pygame.sprite.Group()

    game_map = None  # просто чтоб было
    load_level("data/maps/dev_level.tmx")  # загружаем уровень после того как создали все спрайт-группы

    colliding = [enemies_group, walls_group, players_group]  # группы, которые имеют коллизию

    main()
