import pygame
import sys
import os
import random
import threading
pygame.init()
pygame.mixer.init()


class Everything(pygame.sprite.Sprite):
    def __init__(self, *group, coors, images, loading=True):
        super().__init__(*group)
        self.frames = []
        self.current_frame = 0
        if loading:
            for image in images:
                self.frames.append(load_image(image))
        else:
            for image in images:
                self.frames.append(image)
        self.copy_images = self.frames[:]
        self.image = self.frames[self.current_frame]
        self.rect = self.frames[self.current_frame].get_rect()
        self.rect.x = coors[0]
        self.rect.y = coors[1]

    def destroy_itself(self):
        self.kill()

    def resize_images(self, cell_size):
        for frame in range(len(self.frames)):
            self.frames[frame] = pygame.transform.scale(self.frames[frame], (cell_size - 1, cell_size - 1))
        self.copy_images = self.frames[:]
        self.rect.h = cell_size
        self.rect.w = cell_size

    def update_frame(self):
        self.current_frame += 1
        if len(self.frames) <= self.current_frame:
            self.current_frame = 0
        self.image = self.frames[self.current_frame]


class CanMoveObject(Everything):
    def __init__(self, *group, coors, board_coors, images, const_speed, loading=True):
        super().__init__(*group, coors=coors, images=images, loading=loading)
        self.CONST_SPEED = const_speed
        self.speed = const_speed
        self.new_direction = 0  # +x:1; +y:2; -x:3; -y:4
        self.direction = self.new_direction
        self.health = 1
        self.rendering_changing_direction = False
        self.coors = board_coors

    def random_moving(self, choice):  # +x:1; +y:2; -x:3; -y:4
        self.new_direction = random.choice(choice)
        self.direction = self.new_direction

    def render_direction(self):
        self.frames = []  # +x:1; +y:2; -x:3; -y:4
        # print(self.direction, self.new_direction)
        for image in self.copy_images:

            if self.new_direction == 3:
                self.frames.append(pygame.transform.flip(image, True, False))
            elif self.new_direction == 2:
                self.frames.append(pygame.transform.rotate(image, 270))
            elif self.new_direction == 4:
                self.frames.append(pygame.transform.rotate(image, 90))
            else:
                self.frames.append(image)

        self.image = self.frames[self.current_frame]

    def update(self):
        if not self.rendering_changing_direction:
            if self.direction == 1:
                self.rect.x += self.speed
            elif self.direction == 2:
                self.rect.y += self.speed
            elif self.direction == 3:
                self.rect.x -= self.speed
            elif self.direction == 4:
                self.rect.y -= self.speed


class Hero(CanMoveObject):
    def __init__(self, *group, board_coors, coors):
        self.CONST_SPEED = 3
        self.direction = 1
        self.images = ["Packman/" + file for file in os.listdir("data/Packman")]
        self.invisible = False
        self.active_buffs = []

        super().__init__(*group, coors=coors, images=self.images, board_coors=board_coors, const_speed=self.CONST_SPEED)

    def player_control(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:  #
                self.new_direction = 1
            if event.key == pygame.K_DOWN:  #
                self.new_direction = 2  #
            if event.key == pygame.K_LEFT:  #
                self.new_direction = 3
            if event.key == pygame.K_UP:  #
                self.new_direction = 4  #
            self.render_direction()


class Enemy(CanMoveObject):
    def __init__(self, *group, board_coors, coors):
        self.CONST_SPEED = 3
        self.images = ["Enemy/"+file for file in os.listdir("data/Enemy")]
        self.images_for_directions = {1: [], 2: [], 3: [], 4: []}
        for image in self.images:
            loaded = load_image(image)
            if "down" in image:
                self.images_for_directions[2].append(loaded)
            elif "right" in image:
                self.images_for_directions[3].append(pygame.transform.flip(loaded, True, False))
                self.images_for_directions[1].append(loaded)
            elif "up" in image:
                self.images_for_directions[4].append(loaded)
        super().__init__(*group, board_coors=board_coors, coors=coors, images=self.images_for_directions[1],
                         const_speed=self.CONST_SPEED, loading=False)
        self.direction = 1
        self.new_direction = self.direction

    def resize_images(self, cell_size):  # Потому что есть коллекция с разными направлениями
        for frames in self.images_for_directions.keys():
            new = []
            for frame in self.images_for_directions[frames]:
                new.append(pygame.transform.scale(frame, (cell_size - 1, cell_size - 1)))
            self.images_for_directions[frames] = new
        self.copy_images = self.frames[:]
        self.rect.h = cell_size
        self.rect.w = cell_size

    def render_direction(self):
        if self.new_direction in range(1, 5):
            self.frames = self.images_for_directions[self.new_direction]
        else:
            self.frames = self.images_for_directions[1]
        self.image = self.frames[self.current_frame]


class Buff(Everything):
    def __init__(self, *group, coors, images, loading=True):
        super().__init__(*group, coors=coors, images=images, loading=loading)

    def buff_object(self, object):
        pass

    def activated(self, object):
        self.buff_object(object)
        self.destroy_itself()


class BoostMode(Buff):
    def __init__(self, *group, coors):
        image = load_image("Buff/Boost.png")
        rotated = pygame.transform.rotate(image, 90)
        images = [image, image, image, image, image, image, image, rotated, rotated, rotated, rotated, rotated,
                  rotated, rotated]
        super().__init__(*group, coors=coors, images=images, loading=False)
        self.speed_buff = 1

    def buff_object(self, object):
        object.speed += self.speed_buff


class SpiritMode(Buff):
    def __init__(self, *group, coors):
        image = load_image("Buff/invise.png")
        images = [image]
        self.object = None
        self.picked = False
        self.invisible_active = load_image("Buff/invisible_hero_2.png")
        super().__init__(*group, coors=coors, images=images, loading=False)
        self.SPIRIT_ID = 1
        pygame.time.set_timer(1, 10000)

    def update(self, event):
        if event.type == self.SPIRIT_ID:
            self.object.invisible = False
            self.destroy_itself()

        if self.object is not None:
            self.rect.x = self.object.rect.x
            self.rect.y = self.object.rect.y

        image = self.invisible_active
        self.frames = []

        if self.object.new_direction == 3:
            self.frames.append(pygame.transform.flip(image, True, False))
        elif self.object.new_direction == 2:
            self.frames.append(pygame.transform.rotate(image, 270))
        elif self.object.new_direction == 4:
            self.frames.append(pygame.transform.rotate(image, 90))
        else:
            self.frames.append(image)

        self.update_frame()

    def activated(self, object):
        self.object = object
        self.object.invisible = True
        self.picked = True
        self.buff_object(object)
        self.frames = [self.invisible_active]
        self.copy_images = self.frames[:]

    def resize_images(self, cell_size):
        self.frames[0] = pygame.transform.scale(self.frames[0], (cell_size - 1, cell_size - 1))
        self.copy_images = self.frames[:]
        self.invisible_active = pygame.transform.scale(self.invisible_active,(cell_size - 1, cell_size - 1))
        self.rect.h = cell_size
        self.rect.w = cell_size

    def buff_object(self, object):
        object.invisible = True


class EaterMode(Buff):
    pass


class Game:
    # создание поля
    def __init__(self, level, surface, width, height, cell_size=50):
        self.camera = Camera(width, height)  # main __init__ zone
        self.playing = True
        self.WIDTH = width
        self.HEIGHT = height
        self.LEFT = 0
        self.TOP = 0
        self.CELL_SIZE = cell_size
        self.threading_update = []
        self.started = False

        self.BOOST = load_sound("boost.wav")  # sound zone
        self.LOSE = load_sound("game_over.wav")
        self.INVISE = load_sound("invise.wav")

        tile_images = {'wall': pygame.Surface([self.CELL_SIZE, self.CELL_SIZE]),  # map zone
                       'empty': pygame.Surface([self.CELL_SIZE, self.CELL_SIZE])}
        tile_images["wall"].fill((70, 130, 180))
        tile_images["empty"].fill((176, 196, 222))

        self.BOARD_WIDTH = len(level[0])  # size zone
        self.BOARD_HEIGHT = len(level)

        self.surface = surface
        self.board = level

        self.all_sprites = pygame.sprite.Group()  # sprites zone
        self.everything = pygame.sprite.Group()
        self.title = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.buffs = pygame.sprite.Group()

        self.clear_board = []

        self.score = 0  # score zone
        self.SCORE_TIMER_ID = 20
        pygame.time.set_timer(20, 1000)

        for y in range(self.BOARD_HEIGHT):
            self.clear_board.append([])
            for x in range(self.BOARD_WIDTH):
                if self.board[y][x] == "#":
                    new = Everything(self.all_sprites, self.title, coors=self.get_pixels((x, y)),
                                     images=[tile_images["wall"]], loading=False)
                else:
                    new = Everything(self.all_sprites, self.title, coors=self.get_pixels((x, y)),
                                     images=[tile_images["empty"]], loading=False)

                self.clear_board[-1].append(new)

                if self.board[y][x] == "@":
                    new = self.hero = Hero(self.all_sprites, self.everything, board_coors=(x, y),
                                           coors=self.get_pixels((x, y)))

                elif self.board[y][x] == "e":
                    new = Enemy(self.all_sprites, self.everything, self.enemies, board_coors=(x, y),
                                coors=self.get_pixels((x, y)))

                elif self.board[y][x] == "b":
                    new = BoostMode(self.all_sprites, self.everything, self.buffs, coors=self.get_pixels((x, y)))

                elif self.board[y][x] == "i":
                    new = SpiritMode(self.all_sprites, self.everything, self.buffs, coors=self.get_pixels((x, y)))
                    new.resize_images(cell_size)

                if x == 0 and y == 0:
                    self.start_point = new

        for sprite in self.everything:
            sprite.resize_images(self.CELL_SIZE)

    def get_coors(self, pixels):
        return pixels[0] // self.CELL_SIZE, self.TOP + pixels[1] // self.CELL_SIZE

    def get_coors_on_board_with_bias(self, sprite):
        camera_bias_x = self.start_point.rect.x
        camera_bias_y = self.start_point.rect.y  # +x:1; +y:2; -x:3; -y:4
        return (sprite.rect.x + self.CELL_SIZE//2 - camera_bias_x) // self.CELL_SIZE, \
               (sprite.rect.y + self.CELL_SIZE//2 - camera_bias_y) // self.CELL_SIZE

    def get_pixels(self, coors_on_board):
        return self.LEFT + coors_on_board[0] * self.CELL_SIZE, self.TOP + coors_on_board[1] * self.CELL_SIZE

    def centry_sprite(self, sprite):
        cell_x_on_board, cell_y_on_board = self.get_coors_on_board_with_bias(sprite)
        cell_rect = self.clear_board[cell_y_on_board][cell_x_on_board].rect
        sprite.rect.x = cell_rect.x
        sprite.rect.y = cell_rect.y

    def render(self):
        self.camera.update(self.hero)
        self.title.draw(self.surface)
        self.everything.draw(self.surface)

        for enemy in self.enemies:
            enemy.render_direction()

        for sprite in self.all_sprites:
            self.camera.apply(sprite)
            sprite.update_frame()

        font = pygame.font.Font(None, 80)
        text = font.render(str(self.score), 1, (255, 255, 255))
        rect = text.get_rect()
        rect.x, rect.y = 30, 30
        screen.blit(text, rect)

    def check_direction(self, object, direction):
        r = False
        if direction == 0:
            r = True
        elif direction == 1:  # +x:1; +y:2; -x:3; -y:4
            if self.BOARD_WIDTH > object.coors[0] + 1:
                if self.board[object.coors[1]][object.coors[0]+1] != "#":
                    r = True
        elif direction == 2:
            if self.BOARD_HEIGHT > object.coors[1] + 1:
                if self.board[object.coors[1]+1][object.coors[0]] != "#":
                    r = True
        elif direction == 3:
            if -1 < object.coors[0] - 1:
                if self.board[object.coors[1]][object.coors[0]-1] != "#":
                    r = True
        elif direction == 4:
            if -1 < object.coors[1] - 1:
                if self.board[object.coors[1]-1][object.coors[0]] != "#":
                    r = True
        return r

    def update_hero(self, event):
        self.hero.player_control(event)
        changed_direction = False
        check_new_direction = self.check_direction(self.hero, self.hero.new_direction)
        check_direction = self.check_direction(self.hero, self.hero.direction)

        if check_new_direction and (self.hero.direction != self.hero.new_direction):
            self.hero.direction = self.hero.new_direction
            changed_direction = True
        elif check_direction and self.hero.new_direction == self.hero.direction:
            pass
        elif not check_new_direction and check_direction:
            pass
        else:
            self.hero.direction = 0
            self.hero.new_direction = 0
            changed_direction = True

        if changed_direction:
            self.centry_sprite(self.hero)

        self.hero.update()
        for buff in self.hero.active_buffs:
            buff.update(event)

        self.board[self.hero.coors[1]][self.hero.coors[0]] = '.'
        new_x, new_y = self.get_coors_on_board_with_bias(self.hero)
        self.board[new_y][new_x] = "@"
        self.hero.coors = (new_x, new_y)

        if len(pygame.sprite.spritecollide(self.hero, self.enemies, False)) != 0 and not self.hero.invisible:
            self.LOSE.play()
            self.playing = False

    def update_buffs(self, event):
        collided_buffs = pygame.sprite.spritecollide(self.hero, self.buffs, False)
        for buff in collided_buffs:
            if type(buff) == BoostMode:
                buff.activated(self.hero)
                self.BOOST.play()
                self.score += 20

            elif type(buff) == SpiritMode:
                if not buff.picked:
                    buff.activated(self.hero)
                    self.hero.active_buffs.append(buff)
                    self.INVISE.play()
                    self.score += 20

    def update_enemies(self, event):
        for enemy in self.enemies:
            changed_direction = False
            self.board[enemy.coors[1]][enemy.coors[0]] = '.'
            new_x, new_y = self.get_coors_on_board_with_bias(enemy)  # +x:1; +y:2; -x:3; -y:4
            self.board[new_y][new_x] = "e"
            enemy.coors = (new_x, new_y)
            all_x = [self.board[i][enemy.coors[0]] for i in range(self.BOARD_HEIGHT)]
            if not self.hero.invisible:
                if self.hero.coors[1] == enemy.coors[1] and self.hero.coors[0] == enemy.coors[0]:
                    changed_direction = True
                    enemy.direction = 0
                    enemy.new_direction = 0

                elif self.hero.coors[1] == enemy.coors[1]:

                    if self.hero.coors[0] > enemy.coors[0] \
                            and "#" not in self.board[enemy.coors[1]][enemy.coors[0]:self.hero.coors[0]]:
                        enemy.new_direction = 1

                    elif self.hero.coors[0] < enemy.coors[0] \
                            and "#" not in self.board[enemy.coors[1]][self.hero.coors[0]:enemy.coors[0]]:
                        enemy.new_direction = 3

                elif self.hero.coors[0] == enemy.coors[0]:
                    if self.hero.coors[1] > enemy.coors[1] and "#" not in all_x[enemy.coors[1]:self.hero.coors[1]]:
                        enemy.new_direction = 2

                    elif self.hero.coors[1] < enemy.coors[1] and "#" not in all_x[self.hero.coors[1]:enemy.coors[1]]:
                        enemy.new_direction = 4

            check_new_direction = self.check_direction(enemy, enemy.new_direction)
            check_direction = self.check_direction(enemy, enemy.direction)

            if check_new_direction and (enemy.direction != enemy.new_direction):
                enemy.direction = enemy.new_direction
                changed_direction = True

            elif check_direction and enemy.new_direction == enemy.direction:
                pass

            elif not check_new_direction and check_direction:
                pass

            else:
                cells_for_random_choice = []
                possible_cells = [(0, 1), (1, 0), (-1, 0), (0, -1)]
                make_direction = {(0, -1): 4, (1, 0): 1, (-1, 0): 3, (0, 1): 2}  # +x:1; +y:2; -x:3; -y:4
                for possible in possible_cells:
                    new_x = enemy.coors[0] + possible[0]
                    new_y = enemy.coors[1] + possible[1]
                    if -1 < new_x < self.BOARD_HEIGHT and -1 < new_y < self.BOARD_WIDTH:
                        if self.board[new_y][new_x] != "#":
                            cells_for_random_choice.append(make_direction[possible])
                if len(cells_for_random_choice) != 0:
                    enemy.random_moving(cells_for_random_choice)
                    changed_direction = True

            enemy.update()
            if changed_direction:
                enemy.render_direction()
                self.centry_sprite(enemy)

    def update(self, event):
        if event.type == pygame.KEYDOWN:
            self.started = True
        if event.type == self.SCORE_TIMER_ID and self.hero.direction != 0:
            self.score += 1
        if self.started:
            self.threading_update = [threading.Thread(target=self.update_hero(event)),
                                     threading.Thread(target=self.update_enemies(event)),
                                     threading.Thread(target=self.update_buffs(event))]
            for i in self.threading_update:
                i.start()
            for i in self.threading_update:
                i.join()


class Label:
    def __init__(self, rect, text, font_color=(59, 68, 75), font=None, bgcolor=(240, 248, 255)):
        self.rect = pygame.Rect(rect)
        self.text = text
        if type(bgcolor) == str:
            self.bgcolor = pygame.Color(bgcolor)
        else:
            self.bgcolor = bgcolor

        if type(font_color) == str:
            self.font_color = pygame.Color(font_color)
        else:
            self.font_color = font_color
        # Рассчитываем размер шрифта в зависимости от высоты
        self.font = pygame.font.Font(font, self.rect.height - 4)
        button_text = self.font.render(text, 1, pygame.Color('white'))
        button_rect = button_text.get_rect()
        button_rect.x = rect[0]
        button_rect.y = rect[1]
        button_rect.w += 10
        self.rect.w = button_rect.w
        self.rendered_text = None
        self.rendered_rect = None

    def render(self, surface):
        surface.fill(self.bgcolor, self.rect)
        self.rendered_text = self.font.render(self.text, 1, self.font_color)
        self.rendered_rect = self.rendered_text.get_rect(x=self.rect.x + 2, centery=self.rect.centery)
        # выводим текст
        surface.blit(self.rendered_text, self.rendered_rect)


class Button(Label):
    def __init__(self, rect, text, font_color=(59, 68, 75), font=None, bgcolor=(240, 248, 255)):
        self.CLICK = load_sound("click.wav")
        super().__init__(rect, text, font_color, font, bgcolor)
        # при создании кнопка не нажата
        self.pressed = False

    def render(self, surface):
        surface.fill(self.bgcolor, self.rect)
        self.rendered_text = self.font.render(self.text, 1, self.font_color)
        if not self.pressed:
            color1 = pygame.Color("white")
            color2 = pygame.Color("black")
            self.rendered_rect = self.rendered_text.get_rect(x=self.rect.x + 5, centery=self.rect.centery)
        else:
            color1 = pygame.Color("black")
            color2 = pygame.Color("white")
            self.rendered_rect = self.rendered_text.get_rect(x=self.rect.x + 7, centery=self.rect.centery + 2)

        # рисуем границу
        pygame.draw.rect(surface, color1, self.rect, 2)
        pygame.draw.line(surface, color2, (self.rect.right - 1, self.rect.top),
                         (self.rect.right - 1, self.rect.bottom), 2)
        pygame.draw.line(surface, color2, (self.rect.left, self.rect.bottom - 1),
                         (self.rect.right, self.rect.bottom - 1), 2)
        # выводим текст
        surface.blit(self.rendered_text, self.rendered_rect)

    def get_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.pressed = self.rect.collidepoint(event.pos)
            if self.pressed:
                self.CLICK.play()
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.pressed = False


class TextBox(Label):
    def __init__(self, rect, text, font_color=(59, 68, 75), font=None, bgcolor=(240, 248, 255), max_len=None):
        super().__init__(rect, text, font_color, font, bgcolor)
        self.active = False
        self.blink = True
        self.blink_timer = 20
        self.pos = 0
        self.max_len = max_len
        self.rendered_text_for_line = None
        self.rendered_rect_for_line = None

    def execute(self):
        pass

    def get_event(self, event):
        pressed = pygame.key.get_pressed()
        if event.type == pygame.KEYDOWN and self.active:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.execute()
            elif event.key == pygame.K_BACKSPACE:
                if len(self.text) > 0:
                    self.text = self.text[:self.pos]+self.text[1+self.pos:]
                    self.pos -= 1

            elif pressed[276] and not pressed[275]:  # left
                self.pos -= 1
            elif pressed[275] and not pressed[276]:  # right
                self.pos += 1

            elif event.key != pygame.K_TAB:
                if self.max_len is None:
                    try_text = self.text[:self.pos + 1] + event.unicode + self.text[1 + self.pos:]
                    try_text_render = self.font.render(try_text, 1, self.font_color)
                    text_w = try_text_render.get_width()
                    text_h = try_text_render.get_height()

                    if text_w <= self.rect[2] and text_h <= self.rect[3]:
                        self.pos += 1
                        self.text = try_text

                else:
                    if len(self.text) < self.max_len:
                        self.text = self.text[:self.pos+1] + event.unicode + self.text[1+self.pos:]
                        self.pos += 1

            if self.pos < 0:
                self.pos = len(self.text) - 1
            elif self.pos > len(self.text) - 1:
                pass

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.active = True
            else:
                self.active = False
            self.rendered_text_for_line = self.font.render(self.text[:self.active], 1, self.font_color)
            self.rendered_rect_for_line = self.rendered_text_for_line.get_rect(x=self.rect.x + 2, centery=self.rect.centery)

    def update(self):
        if pygame.time.get_ticks() - self.blink_timer > 300:
            self.blink = not self.blink
            self.blink_timer = pygame.time.get_ticks()

    def render(self, surface):
        self.rendered_text_for_line = self.font.render(self.text[:self.pos+1], 1, self.font_color)
        self.rendered_rect_for_line = self.rendered_text_for_line.get_rect(x=self.rect.x, centery=self.rect.centery)
        super(TextBox, self).render(surface)
        if self.blink and self.active:
            pygame.draw.line(surface, pygame.Color("black"),
                             (self.rendered_rect_for_line.right + 1, self.rendered_rect_for_line.top + 2),
                             (self.rendered_rect_for_line.right + 1, self.rendered_rect_for_line.bottom - 2))


class Camera:
    # зададим начальный сдвиг камеры
    def __init__(self, width, height):
        self.dx = 0
        self.dy = 0
        self.width = width
        self.height = height

    # сдвинуть объект obj на смещение камеры
    def apply(self, obj):
        obj.rect.x += self.dx
        obj.rect.y += self.dy

    # позиционировать камеру на объекте target
    def update(self, target):
        self.dx = -(target.rect.x + target.rect.w // 2 - self.width // 2)
        self.dy = -(target.rect.y + target.rect.h // 2 - self.height // 2)


class GUI:
    def __init__(self):
        self.elements = []

    def add_element(self, element):
        self.elements.append(element)

    def render(self, surface):
        for element in self.elements:
            render = getattr(element, "render", None)
            if callable(render):
                element.render(surface)

    def update(self):
        for element in self.elements:
            update = getattr(element, "update", None)
            if callable(update):
                element.update()

    def get_event(self, event):
        for element in self.elements:
            get_event = getattr(element, "get_event", None)
            if callable(get_event):
                element.get_event(event)


def load_level(filename):
    filename = "data/levels/" + filename
    # читаем уровень, убирая символы перевода строки
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]

    # и подсчитываем максимальную длину
    max_width = max(map(len, level_map))

    # дополняем каждую строку пустыми клетками ('.')
    return [[sym for sym in line] for line in list(map(lambda x: x.ljust(max_width, '.'), level_map))]


def load_image(name):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname)
        image.set_colorkey((255, 255, 255))
        return image
    except pygame.error as message:
        print('Cannot load image:', name)
        raise SystemExit(message)


def load_sound(name):
    fullname = os.path.join('data\\Sounds', name)
    try:
        sound = pygame.mixer.Sound(fullname)
        return sound
    except pygame.error as message:
        print('Cannot load sound:', name)
        raise SystemExit(message)


def terminate():
    pygame.mixer.quit()
    pygame.quit()
    sys.exit()


def tables_screen(surface, width, height):
    with open("data/tables.txt", "r") as file:
        tables = [line.split(';') for line in file.read().strip('\n').split("\n")]

    exit_button = Button([40, height - 120, 80, 80], "Назад")

    surface.fill(pygame.Color('black'))
    image = load_image("background.jpg")
    surface.blit(image, image.get_rect())
    font = pygame.font.Font(None, 50)

    intro = font.render("Таблица рекордов", 1, pygame.Color('green'))
    intro_rect = intro.get_rect()
    intro_rect.x = width // 2 - intro_rect.w // 2
    intro_rect.y = 50
    surface.blit(intro, intro_rect)

    text_coord = 100
    for line in range(len(tables)):

        nickname = font.render(str(line+1)+". "+tables[line][0], 1, (240, 248, 255))
        score = font.render(tables[line][1], 1, (230, 230, 250))

        nickname_rect = nickname.get_rect()
        score_rect = score.get_rect()

        text_coord += 10
        nickname_rect.top = text_coord
        nickname_rect.x = 200
        score_rect.top = text_coord
        score_rect.right = width - 200

        text_coord += nickname_rect.height

        surface.blit(nickname, nickname_rect)
        surface.blit(score, score_rect)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if exit_button.pressed:
                running = False
            exit_button.get_event(event)

        exit_button.render(surface)
        pygame.display.flip()


def rules_screen(surface, width, height):

    surface.fill(pygame.Color('black'))
    image = load_image("background.jpg")
    surface.blit(image, image.get_rect())
    image_size = (60, 60)

    rules_sprites = pygame.sprite.Group()

    me = pygame.sprite.Sprite(rules_sprites)
    me.image = pygame.transform.scale(load_image("Packman/packman3.png"), image_size)
    me.rect = me.image.get_rect()
    me.rect.x = width // 2 - me.rect.w//2

    boost = pygame.sprite.Sprite(rules_sprites)
    boost.image = pygame.transform.scale(load_image("Buff/Boost.png"), image_size)
    boost.rect = boost.image.get_rect()
    boost.rect.x = width // 2 - boost.rect.w // 2

    invise = pygame.sprite.Sprite(rules_sprites)
    invise.image = pygame.transform.scale(load_image("Buff/invise.png"), image_size)
    invise.rect = invise.image.get_rect()
    invise.rect.x = width // 2 - invise.rect.w // 2

    enemy = pygame.sprite.Sprite(rules_sprites)
    enemy.image = pygame.transform.scale(load_image("Enemy/right.png"), image_size)
    enemy.rect = enemy.image.get_rect()
    enemy.rect.x = width // 2 - enemy.rect.w // 2

    rules_text = ["Это - вы, управление происходит ",
                  "при помощи стрелок.",
                  "",
                  "Это - дух, ваш противник, ",
                  "остерегайтесь его, иначе он вас съест!",
                  "",
                  "Это - ускоритель, добаляет ",
                  "вам постоянной скорости.",
                  "",
                  "Это - мантия невидимка, когда ",
                  "надета, духи не видят вас ",
                  "и не могут съесть."]

    font = pygame.font.Font(None, 60)
    start_color = (200, 247, 231)
    text_coord = 100
    for line in range(len(rules_text)):
        if rules_text[line] == "":
            text_coord += image_size[1]
        if line == 0:
            me.rect.y = text_coord - image_size[1]
        elif line == 3:
            enemy.rect.y = text_coord - image_size[1]
        elif line == 6:
            boost.rect.y = text_coord - image_size[1]
        elif line == 9:
            invise.rect.y = text_coord - image_size[1]

        string_rendered = font.render(rules_text[line], 1, (start_color[0], start_color[1], start_color[2]+line))
        line_rect = string_rendered.get_rect()
        text_coord += 10
        line_rect.top = text_coord
        line_rect.x = width // 2 - line_rect.w // 2
        text_coord += line_rect.height
        surface.blit(string_rendered, line_rect)

    exit_button = Button([40, height - 120, 80, 80], "Назад")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if exit_button.pressed:
                running = False
            exit_button.get_event(event)
        rules_sprites.draw(surface)
        exit_button.render(surface)
        pygame.display.flip()


def start_screen(surface, width, height):
    intro_text = ["Главное меню",
                  ""]

    surface.fill(pygame.Color('black'))
    image = load_image("background.jpg")
    surface.blit(image, image.get_rect())
    font = pygame.font.Font(None, 100)
    text_coord = 100
    for line in intro_text:
        string_rendered = font.render(line, 1, (178, 255, 0))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = width//2 - intro_rect.w//2
        text_coord += intro_rect.height
        surface.blit(string_rendered, intro_rect)

    gui = GUI()
    text_coord += 20
    rules_button = Button([10, 10, 40, 80], "Правила игры")  # 3 параметр автоматичен
    rules_button.rect.x = width // 2 - rules_button.rect.w // 2
    rules_button.rect.y = text_coord

    text_coord += 20 + rules_button.rect.h
    tables_button = Button([10, 10, 40, 80], "Таблица рекордов")
    tables_button.rect.x = width // 2 - tables_button.rect.w // 2
    tables_button.rect.y = text_coord

    text_coord += 20 + tables_button.rect.h
    start_button = Button([10, 10, 40, 120], "Начать игру!")  # 3 параметр автоматичен
    start_button.rect.x = width // 2 - start_button.rect.w // 2
    start_button.rect.y = text_coord

    author = Button([10, height-90, 40, 40], "Автор - Dikower", bgcolor=(3, 65, 107), font_color=(227, 239, 247))

    gui.add_element(author)
    gui.add_element(rules_button)
    gui.add_element(start_button)
    gui.add_element(tables_button)

    running = True
    do = None
    times = 0
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if start_button.pressed:
                do = "game"
                running = False
                break
            elif rules_button.pressed:
                do = "rules"
                running = False
                break
            elif tables_button.pressed:
                do = "tables"
                running = False
                break
            elif author.pressed:
                times += 1

            if times >= 200:
                do = "unknown"
                running = False
                break

            gui.get_event(event)
        gui.render(screen)
        gui.update()
        pygame.display.flip()
        # clock.tick(fps)
    return do


def playing(surface, width, height, level_name, cell_size=50):
    level_1 = load_level(level_name)
    game = Game(level_1, surface, width, height, cell_size)
    running_game = True

    while running_game:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()

            if event.type == RENDER_ID_EVENT:
                screen.fill((0, 0, 0))
                game.render()
                pygame.display.flip()

            if event.type != pygame.MOUSEMOTION:
                game.update(event)

        if not game.playing:
            running_game = False
    return game.score


def save_me(surface, score, width, height):
    surface.fill(pygame.Color('black'))
    image = load_image("background.jpg")
    surface.blit(image, image.get_rect())

    font = pygame.font.Font(None, 80)
    score_text = font.render("Твой счет: "+str(score), 1, (153, 102, 204))
    score_rect = score_text.get_rect()
    score_rect.x = width//2 - score_rect.w//2
    score_rect.y = 100
    surface.blit(score_text, score_rect)

    nickname_box = TextBox([10 - 150, 300, 600, 80], "Введите имя...", )
    nickname_box.rect.x = width // 2 - nickname_box.rect.w // 2

    exit_button = Button([10, 400, 80, 80], "Готово")
    exit_button.rect.x = width // 2 - exit_button.rect.w // 2

    gui = GUI()
    gui.add_element(exit_button)
    gui.add_element(nickname_box)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if exit_button.pressed:
                running = False
                if nickname_box.text == "" or nickname_box.text == "Введите имя...":
                    nickname_box.text = "Hello, no_name is here!"
                with open("data/tables.txt") as file:
                    tables = [line.split(';') for line in file.read().strip('\n').split("\n")]

                tables_dict = {}
                for table in tables:
                    tables_dict[int(table[1])] = tables_dict.get(int(table[1]), [])+[table[0]]
                tables_dict[score] = tables_dict.get(score, []) + [nickname_box.text]
                keys = sorted(tables_dict.keys(), reverse=True)
                result = []
                times = 0
                while times < 10:
                    if len(keys) != 0:
                        key = keys.pop(0)
                        for nickname in sorted(tables_dict[key]):
                            if times < 10:
                                result.append(nickname+';'+str(key))
                                times += 1
                            else:
                                break
                        if times >= 10:
                            break
                    else:
                        break
                with open("data/tables.txt", "w") as file:
                    file.write('\n'.join(result))
                break

            gui.get_event(event)
        gui.render(surface)
        gui.update()
        pygame.display.flip()


SIZE = WIDTH, HEIGHT = 1000, 1000  # 1920x1080 - max
screen = pygame.display.set_mode(SIZE)

RENDER_ID_EVENT = 10
pygame.time.set_timer(RENDER_ID_EVENT, 20)


def main():
    while True:
        next = start_screen(screen, WIDTH, HEIGHT)
        if next == "rules":
            rules_screen(screen, WIDTH, HEIGHT)
        elif next == "game":
            score = playing(screen, WIDTH, HEIGHT, level_name="level_1.txt")
            save_me(screen, score, WIDTH, HEIGHT)
        elif next == "tables":
            tables_screen(screen, WIDTH, HEIGHT)
        elif next == "unknown":
            playing(screen, WIDTH, HEIGHT, level_name="level_2.txt")


if __name__ == '__main__':
    main()
