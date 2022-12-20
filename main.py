import os
import sys

import pygame
from pytmx import load_pygame
import pickle
import socket
import threading
import queue
import time
from pathlib import Path


DEFAULT_SERVER_IP = '127.0.0.1'
DEFAULT_SERVER_PORT = 5070
SOCKET_BUFFER_SIZE = 4096
SOCKET_PROTOCOL = socket.SOCK_STREAM

CMD_CREATE = 0
CMD_SYNC = 1

pygame.init()
size = (800, 600)
BGCOLOR = 'white'
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Top Down")
clock = pygame.time.Clock()


def receive_whole_msg(conn: socket.socket, end_msg=b'end'):
    chunk = conn.recv(SOCKET_BUFFER_SIZE)
    chunks = [chunk]
    while chunk != end_msg:
        chunk = conn.recv(SOCKET_BUFFER_SIZE)
        chunks.append(chunk)
    return b''.join(chunks[:-1])  # обрезаем последний т. к. он b'end'


def load_image(name, colorkey=None):
    fullname = name
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
    image_path = Path("data/templates/Obsolete.png")
    image = pygame.transform.scale(load_image(image_path), (32, 32))

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
    image_path = Path("data/templates/arrow.png")
    image = pygame.transform.scale(load_image(image_path), (32, 32))

    # желательно без трансформа, просто сделать мелкий спрайт, но пока сойдет

    def __init__(self, x: int, y: int, nick: str, id_: int, *groups):
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
        self.id = id_
        self.pressed = dict()

    def move(self):
        super(Player, self).move()

        if self.pressed.get(pygame.K_w, False):
            self.movement_vector[1] += -1 * self.movement_speed
        if self.pressed.get(pygame.K_s, False):
            self.movement_vector[1] += 1 * self.movement_speed
        if self.pressed.get(pygame.K_a, False):
            self.movement_vector[0] += -1 * self.movement_speed
        if self.pressed.get(pygame.K_d, False):
            self.movement_vector[0] += 1 * self.movement_speed

        self.collision_test()

    def update(self, *args):
        self.prev_pos = self.pos
        for event in server.get_events(self.id):
            if event.type == pygame.KEYDOWN:
                self.pressed[event.key] = True
            elif event.type == pygame.KEYUP:
                self.pressed[event.key] = False
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
    image_path = Path("data/templates/wall.jpg")
    image = pygame.transform.scale(load_image(image_path), (32, 32))  # РАЗМЕР 1 ПЛИТКИ - 32х32

    def __init__(self, x, y, groups, rect_data, image=None):  # rect_data потом разберусь с ним, пока юзлес
        super().__init__(groups)
        self.pos = [x, y]
        self.image = Wall.image if image is None else image

        self.rect = self.image.get_rect()
        self.rect.height = 5
        self.rect.topleft = self.pos


class Tile(pygame.sprite.Sprite):  # просто плитки, никакой коллизии
    image_path = Path("data/templates/grass.jpg")
    image = pygame.transform.scale(load_image(image_path), (32, 32))  # РАЗМЕР 1 ПЛИТКИ - 32х32

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


class Server:
    def __init__(self, ip: str = DEFAULT_SERVER_IP, port: int = DEFAULT_SERVER_PORT, max_players: int = 3):
        self.socket = socket.socket(socket.AF_INET, SOCKET_PROTOCOL)
        self.socket.bind((ip, port))
        self.players = dict()
        self.events = {i: list() for i in range(max_players)}
        self._incomplete_draw_state = []
        self._send_draw_state = pickle.dumps(self._incomplete_draw_state)
        self.max_players = max_players
        self.unused_player_ids = [i for i in range(max_players)]
        self.socket.listen()
        self.new_players_thread = threading.Thread(target=self.listen_for_new_players)
        self.new_players_thread.start()
        self.handle_outgoing_thread = threading.Thread(target=self.handle_outgoing)
        self.handle_outgoing_thread.start()
        self.ip = ip
        self.port = port

    def listen_for_new_players(self):
        listening = True
        while listening:
            if len(self.players) > self.max_players:
                time.sleep(1)  # спим, чтобы не нагружать особо наверное
                continue
            conn, addr = self.socket.accept()
            time.sleep(0.5)
            # если ничего не получим в течение полусекунды, то нафиг надо
            try:
                conn.setblocking(False)
                data = conn.recv(SOCKET_BUFFER_SIZE)  # выбросит исключение, если сюда ничего не отправили
                conn.setblocking(True)
            except BlockingIOError:
                continue
            if data != b'connect':
                continue
            self.players[addr] = conn
            conn.send(b'connect')
            next_player_id = min(self.unused_player_ids)
            self.unused_player_ids.remove(next_player_id)
            conn.send(next_player_id.to_bytes(64, 'little'))
            thread = threading.Thread(target=self.handle_client, args=(conn, addr, next_player_id))
            thread.start()

    def handle_client(self, conn: socket.socket, addr: tuple[str, int], player_id: int):
        print(f'подключился игрок № {player_id}')
        # спаун
        players_list.append(Player(430, 300, str(player_id), player_id, players_group))
        connected = True
        while connected:
            try:
                event_type, event_dict = pickle.loads(receive_whole_msg(conn))
                print(event_type)
            except ConnectionResetError:
                connected = False
                self.unused_player_ids.append(player_id)
                break
            else:
                self.events[player_id].append(pygame.event.Event(event_type, event_dict))
        print(f'отключился игрок № {player_id}')

    def handle_outgoing(self):
        while True:
            for other_addr, other_conn in self.players.items():
                try:
                    other_conn.send(self._send_draw_state)
                    other_conn.send(b'end')
                except ConnectionResetError:
                    pass

    def get_events(self, player_id: int):
        events: list = self.events[player_id].copy()
        # events.reverse()
        self.events[player_id].clear()
        return events

    def blit(self, image_path: Path, rect: pygame.rect.Rect):
        self._incomplete_draw_state.append({'image_path': image_path, 'rect': rect})

    def draw_group(self, group: pygame.sprite.Group):
        for sprite in group:
            if isinstance(sprite, Pawn):
                self.blit(sprite.image_path, sprite.rect)

    def flip(self):
        self._send_draw_state = pickle.dumps(self._incomplete_draw_state)
        self._incomplete_draw_state.clear()


def find_vector_len(point_a, point_b):  # (x1,y1), (x2,y2)
    return ((point_a[0] - point_b[0]) ** 2 +
            (point_a[1] - point_b[1]) ** 2) ** 0.5


def game_loop():
    global players_list
    exit_condition = False
    finish_game = False

    players_list = []
    # спаун
    # players_list.append(Player(430, 300, 'JOHN CENA', players_group))

    for i in range(4):
        Wall(300 + 32 * i, 300, walls_group, [], None)
    # for _ in range(6):
    #     Enemy(random.randint(0, screen.get_width()),
    #           random.randint(0, screen.get_height()), enemies_group)
    while not finish_game:  # игровой процесс, игра останавливается при условии finish_game == True
        if exit_condition:  # закрываем игру да
            return True
        screen.fill(BGCOLOR)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_condition = True

        for p in players_group:
            p.update(screen)
        for e in enemies_group:
            e.update(screen)

        draw()  # рендерим тут

        server.flip()
        pygame.display.flip()
        # print(clock.get_fps())
        clock.tick(60)


def draw():
    server.draw_group(tile_group)

    all_sprites = [*players_group.sprites(), *enemies_group.sprites(), *deployable_group.sprites(),
                   *items_group.sprites(), *walls_group.sprites()]
    # ТУДА ВСЕ ГРУППЫ!!!(кроме tile_group)
    for spr in sorted(all_sprites, key=lambda x: x.pos[1]):  # сортируем по y и рендерим по убыванию
        server.blit(spr.image_path, spr.rect)


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


if __name__ == '__main__':
    tile_group = pygame.sprite.Group()  # просто плитки, никакой коллизии/взаимодействия
    players_group = pygame.sprite.Group()
    enemies_group = pygame.sprite.Group()
    deployable_group = pygame.sprite.Group()
    items_group = pygame.sprite.Group()
    walls_group = pygame.sprite.Group()

    game_map = None  # просто чтоб было
    load_level("data/maps/dev_level.tmx")  # загружаем уровень после того как создали все спрайт-группы

    colliding = [enemies_group, walls_group, players_group]  # группы, которые имеют коллизию

    server = Server()

    main()
