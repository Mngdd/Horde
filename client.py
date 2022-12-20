import pygame.event
from main import *


def is_image(path: Path):
    return path.parts[-1][-4:] in ('.png', '.jpg', 'jpeg', '.bmp')


images_map = {image_path.relative_to('.').as_posix(): pygame.transform.scale(load_image(image_path), (32, 32))
              for image_path in Path('./data/templates').glob('**/*') if image_path.is_file() and is_image(image_path)}

pygame.init()
size = (800, 600)
BGCOLOR = 'white'
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Top Down")
clock = pygame.time.Clock()


class Client:
    def __init__(self, server_ip: str = DEFAULT_SERVER_IP, server_port: int = DEFAULT_SERVER_PORT):
        self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._conn.connect((server_ip, server_port))  # выбрасывает ConnectionRefusedError, если не получается
        self._conn.send(b'connect')
        if self._conn.recv(SOCKET_BUFFER_SIZE) != b'connect':
            raise ConnectionRefusedError
        self.id = int.from_bytes(self._conn.recv(SOCKET_BUFFER_SIZE), 'little')
        self._next_draw_state = set()
        self._listen_thread = threading.Thread(target=self._listen)
        self._listen_thread.start()

    def _listen(self):
        connected = True
        while connected:
            try:
                self._next_draw_state = pickle.loads(receive_whole_msg(self._conn))
            except pickle.PickleError:
                continue

    def update(self, event: pygame.event.Event):
        self._conn.send(pickle.dumps((event.type, event.__dict__)))
        self._conn.send(b'end')

    def get_draw_state(self) -> set[dict]:
        return self._next_draw_state


def draw():
    global client, screen
    for instruction in client.get_draw_state():
        image_path: str = instruction['image_path'].as_posix()
        rect: pygame.rect.Rect = instruction['rect']
        image: pygame.surface.Surface = images_map[image_path]
        screen.blit(image, rect)
        # print('draw')


def game_loop():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                client.update(event)
        screen.fill(BGCOLOR)
        draw()
        pygame.display.flip()
        clock.tick(60)


if __name__ == '__main__':
    client = Client()
    game_loop()
