import random

import pygame
import pygame_widgets
from pygame_widgets.widget import WidgetBase
from pygame_widgets.button import Button
from pygame_widgets.button import ButtonArray
from pygame_widgets.textbox import TextBox
from pygame_widgets.widget import WidgetBase
from bd import *


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
        self._db = Record()
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

    def play(self, mp, im_a_host, nick, ip_port=None):
        self.destroy()
        self.result = [mp, im_a_host, nick, ip_port]

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
        perk_button = Button(screen, 630, 520, 95, 30, text='Perks', radius=5,
                             onClick=self.show_perks, inactiveColour=Menu.WHITE, font=self.font)
        trinket_button = Button(screen, 630, 460, 95, 30, text='Trinkets', radius=5,
                                onClick=self.show_trinkets, inactiveColour=Menu.WHITE, font=self.font)
        super(StartMenu, self).__init__(
            play_button, settings_button, quit_button, label, perk_button, trinket_button)

    def play_select(self):
        self.destroy()
        self.result = CreateGame(self.screen, self._db).run()

    def settings(self):
        self.destroy()
        self.result = SettingsMenu(self.screen).run()

    def show_perks(self):
        self.destroy()
        self.result = AllPerks(self.screen, self._db).run()

    def show_trinkets(self):
        self.destroy()
        self.result = AllTrinkets(self.screen, self._db).run()


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
    def __init__(self, screen: pygame.surface.Surface, db: Record):
        self._db = db
        back_button = Button(screen, 50, 250, 65, 30, text='Back', radius=5,
                             onClick=self.back, inactiveColour=Menu.WHITE, font=self.font)
        label = Label(screen, 300, 0, 100, 50, text='Start/Join the game...', textColour=Menu.BLACK, font=self.font)
        nick_label = Label(screen, 300, 140, 150, 50, text='Nick:', textColour=Menu.BLACK, font=self.font)
        solo = Button(screen, 50, 100, 65, 30, text='Solo', radius=5,
                      onClick=self.solo, inactiveColour=Menu.WHITE, font=self.font)
        mp = Button(screen, 50, 150, 130, 30, text='Multiplayer', radius=5,
                    onClick=self.mp, inactiveColour=Menu.WHITE, font=self.font)
        self.nickname = TextBox(screen, 400, 150, 135, 30, radius=5, inactiveColour=Menu.WHITE, font=self.font)
        if nick is not None:
            self.nickname.setText(nick)
        super(CreateGame, self).__init__(back_button, solo, mp, self.nickname, label, nick_label)

    def mp(self):
        global nick
        if self.nickname.text:
            nick = ''.join(self.nickname.text)
            self._db.add_nickname(nick)
            self.destroy()
            self.result = Multiplayer(self.screen, self._db).run()

    def solo(self):
        if self.nickname.text:
            self._db.add_nickname(nick)
            self.destroy()
            self.play(False, False, ''.join(self.nickname.text))

    def back(self):
        self.destroy()
        self.result = StartMenu(self.screen).run()


class Multiplayer(Menu):  # помогите
    def __init__(self, screen: pygame.surface.Surface, db: Record):
        self._db = db
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
        self.result = CreateGame(self.screen, self._db).run()

    def fast_connect(self, i: int):
        if self.fast_list[i] != 'None':
            self.ip.setText(self.fast_list[i].split(':')[0])
            self.port.setText(self.fast_list[i].split(':')[1])



class AllTrinkets(Menu):
    def __init__(self, screen: pygame.surface.Surface, db: Record):
        self._db = db
        trinkets = self._db.get_trinkets()
        back_button = Button(screen, 630, 520, 95, 30, text='Back', radius=5,
                             onClick=self.back, inactiveColour=Menu.WHITE, font=self.font)
        trinkets_lbl = Label(screen, 350, 0, 100, 100, text='Trinkets',
                             textColour=Menu.BLACK, font=pygame.font.SysFont('Cascadia Code', 50))

        id = Label(screen, 10, 0, 100, 200, text=f'N', textColour=Menu.BLACK,
                   font=pygame.font.SysFont('Cascadia Code', 28))
        name = Label(screen, 40, 0, 300, 200, text=f'name', textColour=Menu.BLACK,
                     font=pygame.font.SysFont('Cascadia Code', 28))
        description = Label(screen, 260, 0, 350, 200, text=f'description', textColour=Menu.BLACK,
                            font=pygame.font.SysFont('Cascadia Code', 28))

        trinket1_id = Label(screen, 10, 30, 100, 300, text=f'{trinkets[0][0]}.', textColour=Menu.BLACK,
                            font=pygame.font.SysFont('Cascadia Code', 24))
        trinket2_id = Label(screen, 10, 130, 100, 300, text=f'{trinkets[1][0]}.', textColour=Menu.BLACK,
                            font=pygame.font.SysFont('Cascadia Code', 24))
        trinket3_id = Label(screen, 10, 230, 100, 300, text=f'{trinkets[2][0]}.', textColour=Menu.BLACK,
                            font=pygame.font.SysFont('Cascadia Code', 24))

        trinket1_name = Label(screen, 40, 30, 330, 300, text=f'{trinkets[0][1]}', textColour=Menu.BLACK,
                              font=pygame.font.SysFont('Cascadia Code', 24))
        trinket2_name = Label(screen, 40, 130, 300, 300, text=f'{trinkets[1][1]}', textColour=Menu.BLACK,
                              font=pygame.font.SysFont('Cascadia Code', 24))
        trinket3_name = Label(screen, 40, 230, 300, 300, text=f'{trinkets[2][1]}', textColour=Menu.BLACK,
                              font=pygame.font.SysFont('Cascadia Code', 24))

        trinket1_description = Label(screen, 340, 30, 370, 300, text=f'{trinkets[0][2]}', textColour=Menu.BLACK,
                                     font=pygame.font.SysFont('Cascadia Code', 24))
        trinket2_description = Label(screen, 340, 130, 370, 300, text=f'{trinkets[1][2]}', textColour=Menu.BLACK,
                                     font=pygame.font.SysFont('Cascadia Code', 24))
        trinket3_description = Label(screen, 340, 230, 370, 300, text=f'{trinkets[2][2]}', textColour=Menu.BLACK,
                                     font=pygame.font.SysFont('Cascadia Code', 24))
        super(AllTrinkets, self).__init__(back_button, trinkets_lbl, id, name, description, trinket1_id, trinket2_id, trinket3_id,
                                          trinket1_name, trinket2_name, trinket3_name, trinket1_description, trinket2_description, trinket3_description)

    def back(self):
        self.destroy()
        self.result = StartMenu(self.screen).run()


class AllPerks(Menu):
    def __init__(self, screen: pygame.surface.Surface, db: Record):
        self._db = db
        perks = self._db.get_perks()
        useyn_bolt = perks[0][2].split(',')
        back_button = Button(screen, 630, 520, 95, 30, text='Back', radius=5,
                             onClick=self.back, inactiveColour=Menu.WHITE, font=self.font)
        perks_lbl = Label(screen, 350, 0, 100, 100, text='Perks',
                          textColour=Menu.BLACK, font=pygame.font.SysFont('Cascadia Code', 50))

        id = Label(screen, 10, 0, 200, 200, text=f'N', textColour=Menu.BLACK,
                   font=pygame.font.SysFont('Cascadia Code', 28))
        name = Label(screen, 60, 0, 300, 200, text=f'name', textColour=Menu.BLACK,
                     font=pygame.font.SysFont('Cascadia Code', 28))
        description = Label(screen, 260, 0, 300, 200, text=f'description', textColour=Menu.BLACK,
                            font=pygame.font.SysFont('Cascadia Code', 28))

        perk1_id = Label(screen, 10, 30, 200, 300, text=f'{perks[0][0]}.', textColour=Menu.BLACK,
                         font=pygame.font.SysFont('Cascadia Code', 24))
        perk2_id = Label(screen, 10, 130, 200, 300, text=f'{perks[1][0]}.', textColour=Menu.BLACK,
                         font=pygame.font.SysFont('Cascadia Code', 24))
        perk3_id = Label(screen, 10, 230, 200, 300, text=f'{perks[2][0]}.', textColour=Menu.BLACK,
                         font=pygame.font.SysFont('Cascadia Code', 24))

        perk1_name = Label(screen, 60, 30, 300, 300, text=f'{perks[0][1]}', textColour=Menu.BLACK,
                           font=pygame.font.SysFont('Cascadia Code', 24))
        perk2_name = Label(screen, 60, 130, 300, 300, text=f'{perks[1][1]}', textColour=Menu.BLACK,
                           font=pygame.font.SysFont('Cascadia Code', 24))
        perk3_name = Label(screen, 60, 230, 300, 300, text=f'{perks[2][1]}', textColour=Menu.BLACK,
                           font=pygame.font.SysFont('Cascadia Code', 24))

        perk1_description = Label(screen, 300, 30, 300, 300, text=f'{useyn_bolt[0]}', textColour=Menu.BLACK,
                                  font=pygame.font.SysFont('Cascadia Code', 24))
        perk1_description2 = Label(screen, 320, 60, 300, 300, text=f'{useyn_bolt[1]}', textColour=Menu.BLACK,
                                   font=pygame.font.SysFont('Cascadia Code', 24))
        perk2_description = Label(screen, 300, 130, 300, 300, text=f'{perks[1][2]}', textColour=Menu.BLACK,
                                  font=pygame.font.SysFont('Cascadia Code', 24))
        perk3_description = Label(screen, 300, 230, 300, 300, text=f'{perks[2][2]}', textColour=Menu.BLACK,
                                  font=pygame.font.SysFont('Cascadia Code', 24))
        super(AllPerks, self).__init__(back_button, perks_lbl, id, name, description, perk1_id, perk2_id, perk3_id,
                                       perk1_name, perk2_name, perk3_name, perk1_description, perk1_description2, perk2_description, perk3_description)

    def back(self):
        self.destroy()
        self.result = StartMenu(self.screen).run()


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
