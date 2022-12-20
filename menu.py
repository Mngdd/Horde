import pygame
import pygame_widgets
from pygame_widgets.widget import WidgetBase
from pygame_widgets.button import Button
from pygame_widgets.textbox import TextBox
from pygame_widgets.toggle import Toggle
from pygame_widgets.slider import Slider
from pygame_widgets.dropdown import Dropdown


class Label(Button):
    def draw(self):
        if not self._hidden:
            self.textRect = self.text.get_rect()
            self.alignTextRect()
            self.win.blit(self.text, self.textRect)


class Menu:
    PLAY = 'play'
    QUIT = 'quit'

    def __init__(self, *widgets: WidgetBase, bg_color=(0, 0, 0)):
        self.running = False
        self.result = ''
        self.widgets = widgets
        self.bg_color = bg_color
        self.screen = widgets[0].win

    def run(self):
        self.running = True
        while self.running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.destroy()
            self.screen.fill(self.bg_color)
            pygame_widgets.update(events)
            pygame.display.update()
        return self.result

    def play(self):
        self.destroy()
        self.result = self.PLAY

    def quit(self):
        self.destroy()
        self.result = self.QUIT

    def destroy(self):
        self.running = False
        for widget in self.widgets:
            widget.hide()


class StartMenu(Menu):
    font_color = (255, 0, 0)
    font_size = 30

    def __init__(self, screen: pygame.surface.Surface):
        play_button = Button(screen, 50, 50, 100, 30, text='Начать игру', fontSize=self.font_size, radius=5,
                             onClick=self.play, inactiveColour=self.font_color)
        settings_button = Button(screen, 50, 150, 100, 30, text='Настройки', fontSize=self.font_size, radius=5,
                                 onClick=self.settings, inactiveColour=self.font_color)
        quit_button = Button(screen, 50, 200, 100, 30, text='Выйти', fontSize=self.font_size, radius=5,
                             onClick=self.quit,
                             inactiveColour=self.font_color)
        label = Label(screen, 300, 0, 100, 50, text='Название игры', textColour=(255, 0, 0), fontSize=self.font_size)
        super(StartMenu, self).__init__(play_button, settings_button, quit_button, label)

    def settings(self):
        self.destroy()
        self.result = SettingsMenu(self.screen).run()


class SettingsMenu(Menu):
    font_color = (255, 0, 0)
    font_size = 30

    def __init__(self, screen: pygame.surface.Surface):
        back_button = Button(screen, 50, 150, 100, 30, text='Назад', fontSize=self.font_size, radius=5,
                             onClick=self.back,
                             inactiveColour=self.font_color)
        label = Label(screen, 300, 0, 100, 50, text='Настройки', textColour=(255, 0, 0), fontSize=self.font_size)
        super(SettingsMenu, self).__init__(back_button, label)

    def back(self):
        self.destroy()
        self.result = StartMenu(self.screen).run()
