import os
import random
import sys

import pygame

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

    def __init__(self, x, y, *groups):
        super().__init__(*groups)

        self.image = Pawn.image  # надо же чета вставить
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

    def move(self):
        pass  # расчет передвижения, этому классу оно незачем

    def update(self, *args):
        pass

    def fire(self):
        pass  # стрелят


class Player(Pawn):  # игрок
    image = pygame.transform.scale(load_image("templates/arrow.png"), (32, 32))

    # желательно без трансформа, просто сделать мелкий спрайт, но пока сойдет

    def __init__(self, x, y, nick, *groups):
        super().__init__(x, y, *groups)

        self.image = Player.image
        self.rect = self.image.get_rect()

        self.movementSpeed = 5
        self.pos = [x, y]
        self.health = 100  # TODO: ИСПОЛЬЗОВАТЬ СКОРОСТЬ ВМЕСТО ПЕРЕМЕЩНИЯ МОМЕНТАЛЬНОГО
        self.alive = True
        self.nick = nick
        # TODO: нужно оружие
        self.availableWeapons = []
        self.equippedWeapon = None
        self.inventory = []

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
        self.move()
        self.rect.topleft = self.pos


class Enemy(Pawn):  # класс проутивников, от него наследоваться будут подклассы
    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups)
        self.movementSpeed = 2
        self.pos = [x, y]
        self.health = 100
        self.alive = True

    def move(self):
        target = [(p, find_vector_len(self.pos, p.pos)) for p in players_group]  # берем живых игроков
        target = sorted(target, key=lambda x: (x[1], x[0].health, x[0].nick))[0][0]  # кого бьем
        collision_tolerance = 0.1  # к/ф отталкивания при коллизии
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
                self.pos[0] -= e.rect.width * collision_tolerance * (1 if go_left else -1)  # толкаем себя
                self.pos[1] -= e.rect.height * collision_tolerance * (1 if go_up else -1)
                tmp = list(e.rect.topleft)  # толкаем другого чела
                tmp[0] += self.rect.width * collision_tolerance * (-1 if go_left else 1)
                tmp[1] += self.rect.height * collision_tolerance * (-1 if go_up else 1)
                e.rect.topleft = tmp
                # print('COLLIDIN')

    def update(self, *args):
        self.move()
        self.rect.topleft = self.pos


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
        self.movementVector = [0, 0]
        self.movementSpeed = 0

    def interact(self):
        pass


class Wall(pygame.sprite.Sprite):  # стены, от них наверн никого наследовать не надо
    image = pygame.transform.scale(load_image("templates/wall.jpg"), (32, 32))

    def __init__(self, x, y, *groups):
        super().__init__(*groups)
        self.pos = [x, y]
        self.image = Wall.image
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
    exit_condition = False
    finish_game = False

    # спаун
    Player(screen.get_width() // 2, screen.get_height() // 2, 'JOHN CENA', players_group)
    for i in range(4):
        Wall(300 + 32 * i, 120, walls_group)
    for _ in range(6):
        Enemy(random.randint(0, screen.get_width()),
              random.randint(0, screen.get_height()), enemies_group)

    while not finish_game:  # игровой процесс, игра останавливается при условии finish_game == True
        if exit_condition:  # закрываем игру да
            return True
        screen.fill(BGCOLOR)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_condition = True

        # player.update(event) # вызываем внутренний апдейт у плееры
        # (мб можно отсюда даже вызывать, тогда ту строку удалить)

        # рендерим тут
        for p in players_group:
            p.update(screen)
        for e in enemies_group:
            e.update(screen)
        players_group.draw(screen)
        enemies_group.draw(screen)
        deployable_group.draw(screen)
        items_group.draw(screen)
        walls_group.draw(screen)

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
    walls_group = pygame.sprite.Group()

    main()
