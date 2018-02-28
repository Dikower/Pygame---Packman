import os
import pygame
pygame.init()

def load_image(name):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname)
        image.set_colorkey((255,255,255))
        return image
    except pygame.error as message:
        print('Cannot load image:', name)
        raise SystemExit(message)


all_sprites = pygame.sprite.Group()
frames = []
new_direction = 2
screen = pygame.display.set_mode((500, 500))
sprite = pygame.sprite.Sprite(all_sprites)
copy_images = [load_image("Buff/invisible_hero.png")]

for image in copy_images:
    if new_direction == 3:
        frames.append(pygame.transform.flip(image, True, False))
    elif new_direction == 2:
        frames.append(pygame.transform.rotate(image, 270))
    elif new_direction == 4:
        frames.append(pygame.transform.rotate(image, 90))
    else:
        frames.append(image)

sprite.image = frames[0]
sprite.rect = sprite.image.get_rect()
pygame.draw.rect(screen, (0, 0, 0), sprite.rect, 1)
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill((255, 255, 255))
    all_sprites.draw(screen)
    pygame.display.flip()

pygame.quit()
