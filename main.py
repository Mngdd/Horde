import os
import sys
from network import Network
import pygame
from pytmx import load_pygame
from menu import *
import ast
import random
from perks import *
from trinkets import *
from subprocess import Popen

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

        self.multipliers = {'STRENGTH_P': 1, 'STRENGTH_M': 1}  # p плюс, m умножить потом перепишу
        self.trinkets = all_trinkets
        self.perks = []
        # с перками потом еще перепишу, а то чета отдельный список хранить в котором умножают отдельные
        # переменные, как-то неоч, тк есть еще и просто список перков(

        self.overlay_open = False  # для магаза, меню паузы может

    def move(self, server_player=False):
        super(Player, self).move()

        if server_player:
            self.pos = server_player
            print('\t', self.pos)
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

    def check_shop(self):
        global shop
        if pygame.key.get_pressed()[pygame.K_e] and not self.overlay_open:
            if shop.can_access(self):
                shop.open_overlay()
                self.overlay_open = True
        if pygame.key.get_pressed()[pygame.K_ESCAPE] and self.overlay_open:
            shop.close_overlay()
            self.overlay_open = False

    def update(self, *args):
        if not self.overlay_open:
            self.prev_pos = self.pos
            self.move()
        self.check_shop()
        super(Player, self).update()

    def new_perk_add(self, perk):
        perk.use(self)


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
        self.rect.topleft = self.pos
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


class InLevelShop(pygame.sprite.Group):
    def __init__(self, items_coords: list[tuple[int, int]]):
        super(InLevelShop, self).__init__()
        self.items_coords = items_coords
        self.items = []
        self.update_items()

    def update_items(self):
        for item in self.items:
            item.kill()
        self.items = [Item(x * 32, y * 32, self) for x, y in self.items_coords]


class ShopItem(Item):
    def __init__(self, x, y, in_level_shop: InLevelShop):
        super(ShopItem, self).__init__(x, y, in_level_shop)


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
        self.overlay_widgets = [
            ScreenDarken(),
            Button(screen, 600, 500, 70, 30, text='Пистолет 1'),
            ButtonArray(screen, 60, 40, 500, 400, (3, 7))
        ]
        if closed:
            self.close_overlay()

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
    if mp_game:
        net = Network()
    exit_condition = False
    finish_game = False

    players = {}  # {'test': {'online': False, 'ip': -1, 'vars': [None]}}  # тут все игроки

    # спаун
    p = Player(430, 300, 'JOHN CENA', players_group)  # игрк
    players[p.nick] = p.pos
    for i in range(4):
        Wall(300 + 32 * i, 300, walls_group, [], None)
    for _ in range(6):
        Enemy(random.randint(0, screen.get_width()),
              random.randint(0, screen.get_height()), enemies_group)

    while not finish_game:  # игровой процесс, игра останавливается при условии finish_game == True
        if exit_condition:  # закрываем игру да
            return True

        # КАРОЧ ОТПРАВЛЯЮ ОТЕДЛЬНО СЛОВАРЬ ИГРОКОВ ОТДЕЛЬНО СЛОВАРЬ ВРАГОВ
        to_send = [p]  # сюда вписывать то, что клиент отправляет на сервер: себя и все что с ним связано

        if mp_game:
            if im_a_host:  # если игрок хостит сервер - он и обрабатывает всю инфу
                # и посылает через сервер другим пепликсам
                reply = parse_data(send_data(net, players, []))  # отправляем на серв обработанную инфу
            else:  # игрок - клиент(подключился на чужой сервер)
                reply = parse_data(send_data(net, to_send))  # отправляем инфу и получаем ответ серва
                for e in reply[1]:
                    print(e)
            try:  # обновляем инфу об игроках
                for player_nick in reply[0]:
                    if player_nick == p.nick:
                        continue
                    x, y = reply[player_nick]
                    if player_nick not in players:
                        players[player_nick] = Player(x, y, player_nick, players_group)  # другой игрк
                    players[player_nick].move([x, y])
            except Exception as e:
                print('MAIN//', e)

        screen.fill(BGCOLOR)

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                exit_condition = True

        for p in players_group:
            p.update(screen)
        for e in enemies_group:
            e.update(screen)

        draw()  # рендерим тут
        pygame_widgets.update(events)  # чтобы интерфейс поверх всего рисовался

        pygame.display.flip()
        clock.tick(75)


def send_data(net, *data):  # TODO: добавить ожидание перед отключение(чтоб не кикало за любой пустой ответ)
    """
    Send position to server
    :return: None
    """
    reply = net.send(str(data))
    # if reply == '':
    #     raise Exception('ОТВЕТА НЕТ. ОТКЛЮЧЕН')
    return reply


def parse_data(data):
    try:
        d = ast.literal_eval(data)  # TODO: тут тоже доделать
        # print('server replied:', d)
        return d
    except Exception as e:
        print('PARSE//', e)
        return None


def draw():
    tile_group.draw(screen)

    all_sprites = [*players_group.sprites(), *enemies_group.sprites(), *deployable_group.sprites(),
                   *items_group.sprites(), *walls_group.sprites(), *in_level_shop.sprites()]
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
    global game_map, in_level_shop, shop
    game_map = load_pygame(level_name)
    for layer_number, layer in enumerate(game_map.visible_layers):
        if layer.name == 'floor':
            for x, y, surf in layer.tiles():
                Tile(x * 32, y * 32, tile_group, surf)
        if layer.name == 'walls':
            for x, y, surf in layer.tiles():
                Wall(x * 32, y * 32, walls_group, [x * 32, y * 32, surf.get_width(), surf.get_height()], surf)
                try:
                    if game_map.get_tile_properties(x, y, layer_number).get('shop', False):
                        shop = Shop(x * 32, y * 32)
                except AttributeError:
                    pass
        if layer.name == 'shop':
            shop_items_coords = []
            for x, y, surf in layer.tiles():
                Tile(x * 32, y * 32, tile_group, surf)
                try:
                    if game_map.get_tile_properties(x, y, layer_number).get('shop_item', False):
                        shop_items_coords.append((x, y))
                except AttributeError:
                    pass
            in_level_shop = InLevelShop(shop_items_coords)


if __name__ == '__main__':
    mp_game = True  # это сетевая или мультиплеер
    im_a_host = True  # False # чиста для копипаста фолс
    if im_a_host:
        p = Popen([sys.executable, 'server.py'])  # парралельно с игрой запускаем сервер

    tile_group = pygame.sprite.Group()  # просто плитки, никакой коллизии/взаимодействия
    players_group = pygame.sprite.Group()
    enemies_group = pygame.sprite.Group()
    deployable_group = pygame.sprite.Group()
    items_group = pygame.sprite.Group()
    walls_group = pygame.sprite.Group()
    in_level_shop = None
    shop: Shop = None

    game_map = None  # просто чтоб было
    load_level("data/maps/dev_level.tmx")  # загружаем уровень после того как создали все спрайт-группы

    colliding = [enemies_group, walls_group, players_group]  # группы, которые имеют коллизию

    main()
