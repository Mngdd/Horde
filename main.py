import os
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

    def __init__(self, *groups, x, y):
        super().__init__(*groups)

        self.image = Pawn.image  # надо же чета вставить
        self.rect = self.image.get_rect()

        self.pos = (x, y)
        self.health = 0
        self.alive = False
        self.movementVector = [0, 0]
        self.movementSpeed = 0
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

    def __init__(self, *groups, x, y):
        super().__init__(*groups, x=x, y=y)

        self.image = Player.image
        self.rect = self.image.get_rect()

        self.movementSpeed = 5
        self.pos = [x, y]
        self.last_clicked_pos = 0, 0  # в эту точку повернут игрок головой
        self.health = 100
        self.alive = True
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
        self.rect.center = self.pos


class Enemy(Pawn):  # класс проутивников, от него наследоваться будут подклассы
    def __init__(self, x, y):
        super().__init__(x=x, y=y)
        self.image.fill('red')
    # TODO: сделать


class Deployable(Pawn):  # гаджетиы - турели/мины и всякое такое что пассивно наносит урон врагам
    def __init__(self, x, y):
        super().__init__(x=x, y=y)
        self.image.fill('cyan')
    # TODO: сделать


class Item(pygame.sprite.Sprite):  # предметы лежащие на земле, можно подбирать их
    # TODO: спрайт-группу поставить
    def __init__(self, *groups):
        super().__init__(*groups)
        self.image = pygame.Surface([8, 8])  # пока спрайта нет, квадратом заменяю
        self.image.fill('orange')
        self.rect = self.image.get_rect(x=16, y=16)
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


def game_loop():
    exit_condition = False
    finish_game = False

    # спаун игроков
    Player(players_group, x=screen.get_width() // 2, y=screen.get_height() // 2)

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
        players_group.draw(screen)

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
    item = pygame.sprite.Group()

    main()
