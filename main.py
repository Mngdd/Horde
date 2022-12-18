import os
import socket
import sys
import random
import pygame
from multiplayer import Server, Client, Synchronizable, DEFAULT_SERVER_IP, DEFAULT_SERVER_PORT, input_server_credentials

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


class Pawn(pygame.sprite.Sprite, Synchronizable):
    image = pygame.transform.scale(load_image("templates/Obsolete.png"), (32, 32))

    def __init__(self, *groups, x, y):
        pygame.sprite.Sprite.__init__(self, *groups)
        Synchronizable.__init__(self, client, tuple(), {'x': x, 'y': y})

        self.image = Pawn.image  # надо же чета вставить

        self._start_tracking()
        self.rect = self.image.get_rect()
        self.pos = (x, y)
        self.health = 0
        self.alive = False
        self.movementVector = [0, 0]
        self.movementSpeed = 0
        self.look_at = 0, 0  # в эту точку повернут игрок головой
        self.availableWeapons = []
        self.equippedWeapon = None
        self.inventory = []
        self._stop_tracking(False)

    def move(self):
        pass  # расчет передвижения, этому классу оно незачем

    def update(self, *args):
        pass

    def fire(self):
        pass  # стрелят


class Player(Pawn):  # игрок
    image = pygame.transform.scale(load_image("templates/arrow.png"), (32, 32))

    # желательно без трансформа, просто сделать мелкий спрайт, но пока сойдет

    def __init__(self, *groups, x, y, nick):
        super().__init__(*groups, x=x, y=y)
        self._kwargs['nick'] = nick

        self.image = Player.image
        self.is_first = self.client.id == 0
        self.can_move = True

        self._start_tracking()
        self.rect = self.image.get_rect()
        self.movementSpeed = 5
        self.pos = [x, y]
        self.health = 100
        self.alive = True
        self.nick = nick
        # TODO: нужно оружие
        self.availableWeapons = []
        self.equippedWeapon = None
        self.inventory = []
        self._stop_tracking()

    def move(self):
        k = pygame.key.get_pressed()
        if k[pygame.K_w]:
            self.pos[1] += -1 * self.movementSpeed
        if k[pygame.K_s]:
            self.pos[1] += 1 * self.movementSpeed
        if k[pygame.K_a]:
            self.pos[0] += -1 * self.movementSpeed
        if k[pygame.K_d]:
            self.pos[0] += 1 * self.movementSpeed

    def update(self, *args):
        self.sync_from_server()
        if self.can_move:
            self.move()
        self.rect.topleft = self.pos
        self.sync_to_server()


class Enemy(Pawn):  # класс проутивников, от него наследоваться будут подклассы
    def __init__(self, *groups, x, y):
        super().__init__(*groups, x=x, y=y)
        self.movementSpeed = 2
        self.pos = [x, y]
        self.health = 100
        self.alive = True

    def move(self):
        target = [(p, find_vector_len(self.pos, p.pos)) for p in players_group]  # берем живых игроков
        target = sorted(target, key=lambda x: (x[1], x[0].health, x[0].nick))[0][0]  # кого бьем
        m = 0.1  # к/ф отталкивания при коллизии
        if target.pos[1] < self.pos[1]:  # TODO: Добавить тут проверку на коллизию(в выбранной точке никого не будет)
            self.pos[1] += -1 * self.movementSpeed
        if target.pos[1] > self.pos[1]:
            self.pos[1] += 1 * self.movementSpeed
        if target.pos[0] < self.pos[0]:
            self.pos[0] += -1 * self.movementSpeed
        if target.pos[0] > self.pos[0]:
            self.pos[0] += 1 * self.movementSpeed

        for e in enemies_group:
            if e == self:
                continue
            if pygame.sprite.collide_rect(self, e):
                # чтоб не толкать друг в друга, думаем куда толкать
                go_left, go_up = self.rect.x < e.rect.x, self.rect.y < e.rect.y
                self.pos[0] -= e.rect.width * m * (1 if go_left else -1)  # толкаем себя
                self.pos[1] -= e.rect.height * m * (1 if go_up else -1)
                tmp = list(e.rect.topleft)  # толкаем другого чела
                tmp[0] += self.rect.width * m * (-1 if go_left else 1)
                tmp[1] += self.rect.height * m * (-1 if go_up else 1)
                e.rect.topleft = tmp
                # print('COLLIDIN')

    def update(self, *args):
        self.move()
        self.rect.topleft = self.pos


class Deployable(Pawn):  # гаджетиы - турели/мины и всякое такое что пассивно наносит урон врагам
    def __init__(self, *groups, x, y):
        super().__init__(*groups, x=x, y=y)
        self.image.fill('cyan')
    # TODO: сделать


class Item(pygame.sprite.Sprite):  # предметы лежащие на земле, можно подбирать их
    def __init__(self, *groups):
        super().__init__(*groups)
        self.image = Pawn.image  # тк это базовый класс, его не должно быть в игре
        self.rect = self.image.get_rect()
        self.pos = None
        self.name = 'PLACEHOLDER'

        # скорость нужна чтобы предметы разлетались в разные стороны(например при смерти персонажа)
        self.movementVector = [0, 0]
        self.movementSpeed = 0

    def interact(self):
        pass


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
    exit_condition = False
    finish_game = False

    # спаун
    Player(players_group, x=screen.get_width() // 2, y=screen.get_height() // 2, nick='JOHN CENA')
    for _ in range(6):
        Enemy(enemies_group, x=random.randint(0, screen.get_width()),
              y=random.randint(0, screen.get_height()))

    while not finish_game:  # игровой процесс, игра останавливается при условии finish_game == True
        if exit_condition:  # закрываем игру да
            return True
        screen.fill(BGCOLOR)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_condition = True

        # player.update(event) # вызываем внутренний апдейт у плееры
        # (мб можно отсюда даже вызывать, тогда ту строку удалить)

        for cmd in client.get_create_commands():
            new_object = Synchronizable.from_remote(*cmd[1:], globals_=globals())
            if isinstance(new_object, Player):
                new_object.can_move = False
                players_group.add(new_object)
                print(new_object.id)
            # if isinstance(new_object, Enemy):
            #     enemies_group.add(new_object)
            # if isinstance(new_object, Deployable):
            #     enemies_group.add(deployable_group)
            # if isinstance(new_object, Item):
            #     enemies_group.add(items_group)

        # рендерим тут
        for p in players_group:
            p.update(screen)
        for e in enemies_group:
            e.update(screen)
        players_group.draw(screen)
        enemies_group.draw(screen)
        deployable_group.draw(screen)
        items_group.draw(screen)

        pygame.display.flip()
        clock.tick(120)


def main():
    done = game_loop()
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.K_SPACE:  # TODO: сделать выход из гейм лупа сюда!
                game_loop()


if __name__ == '__main__':
    players_group = pygame.sprite.Group()
    enemies_group = pygame.sprite.Group()
    deployable_group = pygame.sprite.Group()
    items_group = pygame.sprite.Group()
    server_ip, server_port = input_server_credentials()
    valid_crenedtials = False
    while not valid_crenedtials:
        try:
            client = Client(server_ip, server_port)
        except ConnectionRefusedError:
            print('не удалось подключиться, попробуйте ввести другой сервер')
            server_ip, server_port = input_server_credentials(False)
        else:
            valid_crenedtials = True

    main()
