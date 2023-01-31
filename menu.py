import random

import pygame
import pygame_widgets
from pygame_widgets.widget import WidgetBase
from pygame_widgets.button import Button
from pygame_widgets.button import ButtonArray
from pygame_widgets.textbox import TextBox
from pygame_widgets.widget import WidgetBase


class Label(Button):
    def draw(self):
        if not self._hidden:
            self.textRect = self.text.get_rect()
            self.alignTextRect()
            self.win.blit(self.text, self.textRect)


class Menu:
    PLAY = 'play'
    QUIT = 'quit'
    WHITE, BLACK, D_GRAY, L_GRAY = (255, 255, 255), (0, 0, 0), (87, 87, 87), (180, 180, 180)
    pygame.font.init()
    font = pygame.font.SysFont('Cascadia Code', 30)

    def __init__(self, *widgets: WidgetBase, bg_color=(255, 255, 255)):
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

    def play(self, mp, im_a_host, nick, ip_port=None, level='dev_level.tmx'):
        self.destroy()
        self.result = [mp, im_a_host, nick, ip_port, level]

    def quit(self):
        self.destroy()
        self.result = self.QUIT
        pygame.quit()

    def destroy(self):
        self.running = False
        for widget in self.widgets:
            widget.hide()


class StartMenu(Menu):
    def __init__(self, screen: pygame.surface.Surface):
        play_button = Button(screen, 50, 100, 95, 30, text='Play', radius=5,
                             onClick=self.play_select, inactiveColour=Menu.WHITE, font=self.font)
        settings_button = Button(screen, 50, 150, 135, 30, text='Settings', radius=5,
                                 onClick=self.settings, inactiveColour=Menu.WHITE, font=self.font)
        quit_button = Button(screen, 50, 200, 95, 30, text='Exit', radius=5,
                             onClick=self.quit, inactiveColour=Menu.WHITE, font=self.font)
        label = Label(screen, 100, 30, 100, 50, text='Horde', textColour=Menu.BLACK,
                      font=pygame.font.SysFont('Cascadia Code', 50))
        super(StartMenu, self).__init__(play_button, settings_button, quit_button, label)

    def play_select(self):
        self.destroy()
        self.result = CreateGame(self.screen).run()

    def settings(self):
        self.destroy()
        self.result = SettingsMenu(self.screen).run()


class EndMenu(Menu):
    def __init__(self, screen: pygame.surface.Surface, money: int):
        # to_main_menu_button = Button(screen, 50, 100, 95, 30, text='Play', radius=5,
        #                      onClick=self.to_main_menu, inactiveColour=Menu.WHITE, font=self.font)
        # settings_button = Button(screen, 50, 150, 135, 30, text='Settings', radius=5,
        #                          onClick=self.settings, inactiveColour=Menu.WHITE, font=self.font)
        quit_button = Button(screen, 50, 200, 95, 30, text='Exit', radius=5,
                             onClick=self.quit, inactiveColour=Menu.WHITE, font=self.font)
        label = Label(screen, 100, 30, 100, 50, text=f'Денег: {money}', textColour=Menu.BLACK,
                      font=pygame.font.SysFont('Cascadia Code', 50))
        super(EndMenu, self).__init__(quit_button, label)


class SettingsMenu(Menu):
    def __init__(self, screen: pygame.surface.Surface):
        back_button = Button(screen, 50, 150, 100, 30, text='Back', radius=5,
                             onClick=self.back, inactiveColour=Menu.WHITE, font=self.font)
        label = Label(screen, 300, 0, 100, 50, text='Settings', textColour=Menu.BLACK, font=self.font)
        super(SettingsMenu, self).__init__(back_button, label)

    def back(self):
        self.destroy()
        self.result = StartMenu(self.screen).run()


class CreateGame(Menu):
    def __init__(self, screen: pygame.surface.Surface):
        back_button = Button(screen, 50, 250, 65, 30, text='Back', radius=5,
                             onClick=self.back, inactiveColour=Menu.WHITE, font=self.font)
        label = Label(screen, 300, 0, 100, 50, text='Start/Join the game...', textColour=Menu.BLACK, font=self.font)
        nick_label = Label(screen, 300, 140, 150, 50, text='Nick:', textColour=Menu.BLACK, font=self.font)
        level_label = Label(screen, 300, 260, 150, 50, text='Level:', textColour=Menu.BLACK, font=self.font)
        level1_btn = Button(screen, 340, 300, 30, 30, text='1', radius=5,
                      onClick=self.select_level('dev_level.tmx'), inactiveColour=Menu.WHITE, font=self.font)
        level2_btn = Button(screen, 380, 300, 30, 30, text='2', radius=5,
                            onClick=self.select_level('level2.tmx'), inactiveColour=Menu.WHITE, font=self.font)
        self.level = 'dev_level.tmx'
        solo = Button(screen, 50, 100, 65, 30, text='Solo', radius=5,
                      onClick=self.solo, inactiveColour=Menu.WHITE, font=self.font)
        mp = Button(screen, 50, 150, 130, 30, text='Multiplayer', radius=5,
                    onClick=self.mp, inactiveColour=Menu.WHITE, font=self.font)
        self.nickname = TextBox(screen, 400, 150, 135, 30, radius=5, inactiveColour=Menu.WHITE, font=self.font)
        if nick is not None:
            self.nickname.setText(nick)
        super(CreateGame, self).__init__(back_button, solo, mp, self.nickname, label, nick_label, level_label, level1_btn, level2_btn)

    def select_level(self, level_name: str):
        def inner():
            self.level = level_name
        return inner

    def mp(self):
        global nick
        if self.nickname.text:
            nick = ''.join(self.nickname.text)
            self.destroy()
            self.result = *Multiplayer(self.screen).run(), self.level

    def solo(self):
        if self.nickname.text:
            self.destroy()
            self.play(False, False, ''.join(self.nickname.text), None, self.level)

    def back(self):
        self.destroy()
        self.result = StartMenu(self.screen).run()


class Multiplayer(Menu):  # помогите
    def __init__(self, screen: pygame.surface.Surface):
        global nick
        import json
        self.fast_list = json.load(open('FAV_SERVERS.txt', 'r', encoding='utf-8'))
        self.fast_list = ['None' if self.fast_list['1'][i] == 0 else
                          self.fast_list['1'][i] for i in range(len(self.fast_list['1']))]
        user_ip, user_port = get_ip_port()

        create = Button(screen, 50, 200, 85, 30, text='Create', radius=5,
                        onClick=lambda: self.play(True, True, nick, [user_ip, user_port]),
                        inactiveColour=Menu.WHITE, font=self.font)
        con = Button(screen, 50, 100, 100, 30, text='Connect', radius=5,
                     onClick=lambda: self.connect(self.ip.text, self.port.text), inactiveColour=Menu.WHITE,
                     font=self.font)
        label = Label(screen, 300, 0, 100, 50, text='Find/Create multiplayer game...', textColour=Menu.BLACK,
                      font=self.font)

        fast_game = Label(screen, 600, 50, 100, 50, text='Fast connect:',
                          textColour=Menu.BLACK, font=self.font)
        fast_game2 = Label(screen, 600, 25, 100, 50, text='(add server in settings!)',
                           textColour=Menu.D_GRAY, font=self.font)
        fast_b1 = Button(screen, 550, 100, 200, 30, text=self.fast_list[0], radius=5,
                         onClick=lambda: self.fast_connect(0), inactiveColour=Menu.L_GRAY, font=self.font)
        fast_b2 = Button(screen, 550, 150, 200, 30, text=self.fast_list[1], radius=5,
                         onClick=lambda: self.fast_connect(1), inactiveColour=Menu.L_GRAY, font=self.font)
        fast_b3 = Button(screen, 550, 200, 200, 30, text=self.fast_list[2], radius=5,
                         onClick=lambda: self.fast_connect(2), inactiveColour=Menu.L_GRAY, font=self.font)

        back_button = Button(screen, 50, 325, 65, 30, text='Back', radius=5,
                             onClick=self.back, inactiveColour=Menu.WHITE, font=self.font)
        self.ip = TextBox(screen, 100, 150, 165, 30, radius=5, inactiveColour=Menu.WHITE, font=self.font)
        self.port = TextBox(screen, 330, 150, 135, 30, radius=5, inactiveColour=Menu.WHITE, font=self.font)

        txt_ip = Label(screen, 30, 140, 100, 50, text='ip:',
                       textColour=Menu.D_GRAY, font=self.font)
        txt_port = Label(screen, 250, 140, 100, 50, text='port:', textColour=Menu.D_GRAY, font=self.font)

        ip_my = Label(screen, 350, 225, 100, 50, text=f'{user_ip}', textColour=Menu.BLACK, font=self.font)
        port_my = Label(screen, 100, 250, 100, 50, text=f'{user_port}', textColour=Menu.BLACK, font=self.font)

        txt_ip_my = Label(screen, 150, 225, 100, 50, text='Your server will run on ip:',
                          textColour=Menu.D_GRAY, font=self.font)
        txt_port_my = Label(screen, 50, 250, 100, 50, text='port:', textColour=Menu.D_GRAY, font=self.font)
        line = Label(screen, 160, 165, 150, 50, text='——————————————————',
                     textColour=Menu.D_GRAY, font=self.font)
        super(Multiplayer, self).__init__(create, con, label, back_button, self.ip, ip_my, self.port, port_my,
                                          txt_ip_my, txt_port_my, txt_ip, txt_port, line, fast_game, fast_game2,
                                          fast_b1, fast_b2, fast_b3)

    def connect(self, ip, port):
        if ip and port:
            self.play(True, False, nick, [''.join(ip), ''.join(port)])

    def back(self):
        self.destroy()
        self.result = CreateGame(self.screen).run()

    def fast_connect(self, i: int):
        if self.fast_list[i] != 'None':
            self.ip.setText(self.fast_list[i].split(':')[0])
            self.port.setText(self.fast_list[i].split(':')[1])


def get_ip_port():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    me = s.getsockname()[0]
    s.close()
    port = f"5{''.join((str(random.randint(0, 9)) for _ in range(3)))}"
    with open('SERVER_PORT.txt', mode='w', encoding='utf-8') as f:
        f.write(me+'\n'+port)
    return me, port


nick = None
