import pygame



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





