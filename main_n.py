import os
import sys
from network import Network
import pygame
from pytmx import load_pygame
import ast
import math

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
    image = pygame.transform.scale(load_image("/home/nastya/Documents/code/pygame_project/Horde/data/templates/Obsolete.png"), (32, 32))

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
    image = pygame.transform.scale(load_image("/home/nastya/Documents/code/pygame_project/Horde/data/templates/arrow.png"), (32, 32))

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

    def move(self):
        super(Player, self).move()

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
    image = pygame.transform.scale(load_image("/home/nastya/Documents/code/pygame_project/Horde/data/templates/wall.jpg"), (32, 32))  # РАЗМЕР 1 ПЛИТКИ - 32х32

    def __init__(self, x, y, groups, rect_data, image=None):  # rect_data потом разберусь с ним, пока юзлес
        super().__init__(groups)
        self.pos = [x, y]
        self.image = Wall.image if image is None else image

        self.rect = self.image.get_rect()
        self.rect.height = 5
        self.rect.topleft = self.pos


class Tile(pygame.sprite.Sprite):  # просто плитки, никакой коллизии
    image = pygame.transform.scale(load_image("/home/nastya/Documents/code/pygame_project/Horde/data/templates/grass.jpg"), (32, 32))  # РАЗМЕР 1 ПЛИТКИ - 32х32

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


# class Projectile(pygame.sprite.Sprite):  # пуля сама
#     def __init__(self, *groups):
#         super().__init__(*groups)
class Projectile(pygame.sprite.Sprite):  # пуля сама
    '''
     при коллизии с другим объектом узнает какого этот чел класса  и если надо - снимает хп у него
    '''
    def __init__(self, source, target, speed, lifetime, color, *groups): # откуда, куда, скорость, сколько длится жизнь пули, цвет        super().__init__(*groups)
        super.__init__()
        self.image = pygame.Surface([4, 4])
        self.image.set_colorkey(pygame.Color('black'))
        self.rect = self.image.get_rect(x=source[0], y=source[1])
        pygame.draw.circle(self.image, color,
                           (self.rect.width // 2, self.rect.height // 2),
                           self.rect.width // 2)
        
    
    def meet(self, bullet, enemy) -> str:
        if pygame.sprite.spritecollide(bullet, enemy, False, pygame.sprite.collide_rect):
            return enemy.__name__


    def hit(self, bullet, enemy):
        if self.meet(bullet, enemy) == 'Enemy':
            # self.health -= 1 # типо нужно вычитать какое-то колво хп у противника
            ...

    def freeze(self, bullet, enemy):
        if self.meet(bullet, enemy) == 'Enemy':
            ...


def find_vector_len(point_a, point_b):  # (x1,y1), (x2,y2)
    return ((point_a[0] - point_b[0]) ** 2 +
            (point_a[1] - point_b[1]) ** 2) ** 0.5


def game_loop():
    if mp_game:
        net = Network()
    exit_condition = False
    finish_game = False

    players_list = []
    # спаун
    p = Player(430, 300, 'JOHN CENA', players_group)  # игрк

    for i in range(4):
        Wall(300 + 32 * i, 300, walls_group, [], None)
    # for _ in range(6):
    #     Enemy(random.randint(0, screen.get_width()),
    #           random.randint(0, screen.get_height()), enemies_group)

    while not finish_game:  # игровой процесс, игра останавливается при условии finish_game == True
        if exit_condition:  # закрываем игру да
            return True

        # TODO: ПОЛУЧАТЬ ВРАГОВ ТОЖЕ
        if mp_game:
            players_list = parse_data(send_data(p.pos, net))  # пока отправляем только корды игркв
            for player in players_list:
                print(player.pos)

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
    except:
        return None


def draw():
    tile_group.draw(screen)

    all_sprites = [*players_group.sprites(), *enemies_group.sprites(), *deployable_group.sprites(),
                   *items_group.sprites(), *walls_group.sprites()]
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





class Weapon(pygame.sprite.Sprite):
    """
    оружия: 
    дальники: пистолет, шелли, байрон еще если надо
    ближники: катана, лопата, палка
    написаны в порядке убывания, типо катана самый мощный ближник и тп
    """
    def __init__(self, *groups):
        super().__init__(*groups)
        self.curr_mag_ammo = 0  # сколько патрон ща в магазе
        self.mag_capacity = 0  # сколько влазит в магаз
        self.ammo_max = 0  # сколько можно хранить патрон для этого оружия(без учета магаза)
        # (мб переделать типа патроны не индивидуально хранятся, а в инвентаре)
        self.all_ammo_current = 0  # скока ща всего патрон (без учета магаза)
        self.fire_rate = 0.0  # темп
        
        self.name = 'NONE'
        self.rarity = None  # типа редкое\легендарное\эпичное и тп
        self.last_shot = 0
        self.munition = 100 # колво патронов 
        self.munitionTime = 2000 # колво милисекунд, в течении которого оружие перезаряжается
    
    def normalize_vector(vector):
        """
        расстояние между точками, то есть между врагом и юзером
        """
        if vector == [0, 0]:
            return [0, 0]    
        pythagoras = math.sqrt(vector[0]*vector[0] + vector[1]*vector[1])
        return (vector[0] / pythagoras, vector[1] / pythagoras)
    
    @staticmethod
    def rotate_vector(vector, corner):
        """
        это тоже расстояние между врагом и юзером, только тут еще разброс на какой-то угол,
        если мы хотим потом использовать оружие которое стреляет как шелли из бравл старса
        """
        resultVector = (vector[0] * math.cos(corner)
                        - vector[1] * math.sin(corner),
                        vector[0] * math.sin(corner)
                        + vector[1] * math.cos(corner))
        return resultVector

    def shoot(self):
        """
        выстрел оружия
        """
        pass
    

class Gun(Weapon):
    def __init__(self):
        super.__init__()
        self.weapon_cooldown = 100 # тут задержка какая-то, оружие же нагревается
        self.spread = 10  # разброс
    
    def shoot(self, user, mousePos):
        currentTime = pygame.time.get_ticks()
        if self.munition == 0: # тип перезарядка
            if currentTime - self.last_shot > self.munitionTime:
                self.munition = 100
            else:
                return
        
        self.munition -= 1 # минус патрон
        if currentTime - self.last_shot > self.weapon_cooldown:
            direction = (mousePos[0] - user.pos[0], mousePos[1] - user.pos[1]) \
                if mousePos != user.pos else (1, 1)
            self.last_shot = currentTime
            corner = math.radians(random.random()*self.spread - self.spread/2)
            projDir = super().rotate_vector(direction, corner)
            # тут кароче надо как-то вызвать уже projectile  
            bullet = Projectile(user.pos, super().normalize_vector(projDir), 6, 1000, (255, 0, 0), projectiles_group)
            # это кнш не совсем то, надо доделать


class SpreadGun(Weapon):
    """
    как шелли стреляет
    """
    def __init__(self):
        super().__init__()
        self.weapon_cooldown = 750
        self.spread = 75
        self.count_bullets = 7 # сколько пуль в разбросе
        
    def shoot(self, user, mousePos):
        currentTime = pygame.time.get_ticks()
        if self.munition == 0: # тип перезарядка
            if currentTime - self.last_shot > self.munitionTime:
                self.munition = 100
            else:
                return
        
        self.munition -= self.count_bullets # минус патроны
        if currentTime - self.last_shot > self.weapon_cooldown:
            direction = (mousePos[0] - user.pos[0], mousePos[1] - user.pos[1]) \
                if mousePos != user.pos else (1, 1)
            self.last_shot = currentTime
            arcDifference = self.spread / (self.count_bullets - 1)
            for proj in range(self.count_bullets):
                corner = math.radians(arcDifference*proj - self.spread/2)
                projDir = super().rotate_vector(direction, corner)
            # тут кароче надо как-то вызвать уже projectile  
            bullet = Projectile(user.pos, super().normalize_vector(projDir), 6, 1000, (255, 0, 0), projectiles_group)


class FreezeGun(Weapon):
    # надо доделать торможение!!!!!!
    def __init__(self):
        super.__init__()
        self.weapon_cooldown = 50 
        # мне кажется нужно тут делать большую задержку, тип оружие имбовое и ему нужно много времени
        # но урона у врагов он забирает тип много
        self.spread = 5  # разброс маленький
        # кароче будет работать как у байрона в бравл старсе
    
    def shoot(self, user, mousePos):
        currentTime = pygame.time.get_ticks()
        if self.munition == 0: # тип перезарядка
            if currentTime - self.last_shot > self.munitionTime:
                self.munition = 100
            else:
                return
        
        self.munition -= 1 # минус патрон
        if currentTime - self.last_shot > self.weapon_cooldown:
            direction = (mousePos[0] - user.pos[0], mousePos[1] - user.pos[1]) \
                if mousePos != user.pos else (1, 1)
            self.last_shot = currentTime
            corner = math.radians(random.random()*self.spread - self.spread/2)
            projDir = super().rotate_vector(direction, corner)
            bullet = Projectile(user.pos, super().normalize_vector(projDir), 6, 1000, (255, 0, 0), projectiles_group)



if __name__ == '__main__':
    mp_game = True  # это сетевая или мультиплеер

    tile_group = pygame.sprite.Group()  # просто плитки, никакой коллизии/взаимодействия
    players_group = pygame.sprite.Group()
    enemies_group = pygame.sprite.Group()
    deployable_group = pygame.sprite.Group()
    items_group = pygame.sprite.Group()
    walls_group = pygame.sprite.Group()
    projectiles_group = pygame.sprite.Group()

    game_map = None  # просто чтоб было
    load_level("data/maps/dev_level.tmx")  # загружаем уровень после того как создали все спрайт-группы

    colliding = [enemies_group, walls_group, players_group]  # группы, которые имеют коллизию

    main()
