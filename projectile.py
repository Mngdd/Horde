import pygame



class Projectile(pygame.sprite.Sprite):  # пуля сама

    def __init__(self, source, target, speed, lifetime, color, *groups): # откуда, куда, скорость, сколько длится жизнь пули, цвет        
        super.__init__()
        self.image = pygame.Surface([4, 4])
        self.image.set_colorkey(pygame.Color('black'))
        self.rect = self.image.get_rect(x=source[0], y=source[1])
        pygame.draw.circle(self.image, color,
                           (self.rect.width // 2, self.rect.height // 2),
                           self.rect.width // 2)
        self.pos = [source[0], source[1]]
        self.movement_vector = [target[0], target[1]]
        self.speed = speed
        self.lifetime = lifetime
        self.when_created = pygame.time.get_ticks()

    def move(self, surface, time): # размер экрана и время
        if pygame.time.get_ticks() > self.when_created + self.lifetime:
            self.kill() # пуля исчезает, если время ее жизни истекло
        self.pos[0] += self.movement_vector[0] * self.speed * time 
        self.pos[1] += self.movement_vector[1] * self.speed * time
        self.rect.topleft = self.pos
        # я не уверена, по идее это должно давать нам следующую координату
        if self.pos[0] > surface[0] or self.pos[0] < 0  or \
           self.pos[1] > surface[1] or self.pos[1] < 0:
            self.kill() # если пуля вышла за пределы экрана - исчезает
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
            ... # надо замедлять противника





