import pygame

pygame.init()
size = (800, 600)
BGCOLOR = 'white'
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Top Down")
clock = pygame.time.Clock()


class Pawn(pygame.sprite.Sprite):
    def __init__(self, *groups, x, y):
        super().__init__(*groups)

        self.image = pygame.Surface([8, 8])  # пока спрайта нет, квадратом заменяю
        self.image.fill('black')
        self.rect = self.image.get_rect(x=8, y=8)

        self.pos = [x, y]
        self.health = 0
        self.alive = False
        self.movementVector = [0, 0]
        self.movementSpeed = 0
        self.availableWeapons = []
        self.equippedWeapon = None
        self.inventory = []

    def move(self):
        pass  # передвижение тут сделать

    def render(self, sc):
        sc.blit(self.image, self.pos)  # рендер персонажа

    def fire(self):
        pass  # стрелят


class Player(Pawn):  # игрок
    pass


class Enemy(Pawn):  # класс проутивников, от него наследоваться будут подклассы
    def __init__(self, x, y):
        super().__init__(x=x, y=y)
        self.image.fill('red')


class Deployable(Pawn):  # гаджетиы - турели/мины и всякое такое что пассивно наносит урон врагам
    def __init__(self, x, y):
        super().__init__(x=x, y=y)
        self.image.fill('cyan')


class Item:  # предметы лежащие на земле, можно подбирать их
    # TODO: группу поставить
    def __init__(self):
        self.image = pygame.Surface([8, 8])  # пока спрайта нет, квадратом заменяю
        self.image.fill('orange')
        self.rect = self.image.get_rect(x=16, y=16)
        self.pos = None
        self.name = 'PLACEHOLDER'

        # скорость нужна чтобы предметы разлетались в разные стороны(например при смерти персонажа)
        self.movementVector = [0, 0]
        self.movementSpeed = 0

    def render(self, sc):
        sc.blit(self.image, self.pos)


def game_loop():
    exit_condition = False
    finish_game = False

    # спаун игроков
    Player(players_group, x=screen.get_width() // 2, y=screen.get_height() // 2)

    while not finish_game:  # игровой процесс, игра останавливается при условии finish_game == True
        if exit_condition:  # закрываем игру да
            return True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_condition = True

        pass  # обрабатываем события (нажатие клавиш, получение дамага и всякое такое)

        # player.update(event) # вызываем внутренний апдейт у плееры
        # (мб можно отсюда даже вызывать, тогда ту строку удалить)

        # рендерим тут
        for p in players_group:
            p.render(screen)
        players_group.draw(screen)

        screen.fill(BGCOLOR)
        pygame.display.flip()
        clock.tick(120)


def main():
    done = game_loop()
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.K_SPACE:  # рестарт игры яхз как сделать
                game_loop()


if __name__ == '__main__':
    players_group = pygame.sprite.Group()
    enemies_group = pygame.sprite.Group()
    deployable_group = pygame.sprite.Group()
    item = pygame.sprite.Group()

    main()
