from classes import *
from sys import exit
import pygame as pg
import random as rnd
pg.init()


# создание статичных объектов
def Stone(x, y):
    Object(Map, (x, y), (1, 1), -1, ROCK_IMG)
# конец создания стаичных объектов


# код игры для одного игрока
def single_player():
    global Map
    start = [10, 10]  # стартовые координаты левого угла
    # флаги
    hero_movable = True
    hero_attacked = False
    # генерация карты
    Map = [[BasicTile(rnd.choice(GRASS_IMG))for i in range(Map_size_y)] for j in range(Map_size_x)]  # карта объектов (физическая)
    # объекты поля
    # границы
    for i in range(Map_size_x):
        for j in range(MS_visible_y // 2):
            Stone(i, j)
            Stone(i, Map_size_y - j - 1)
    for i in range(Map_size_y):
        for j in range(MS_visible_x // 2):
            Stone(j, i)
            Stone(Map_size_x - j - 1, i)
    # hero
    hero = Hero(Map, (start[0] + MS_visible_x // 2 - 1, start[1] + MS_visible_y // 2 - 1), (2, 2), 101, 4, 10, 5, 20, HERO_ANIMATIONS)
    hero_pl = hero.img.get_rect(center=(sc.get_width() // 2, sc.get_height() // 2))
    # enemies
    Unit(Map, (32, 31), (1, 1), 2, Unit_test_img, 0, 0, 0, 30, Unit_test_dead)
    # конец генерации

    # таймеры
    max_FPS = 60
    FPS = max_FPS
    pg.time.set_timer(27, 1000 // FPS)

    dirr = [0, 0]  # направление движения
    d_pix = [0, 0]
    LK_pix = [-TILE_SIZE, -TILE_SIZE]  # расположение левого верхнего угла области отрисовки пиксельно
    LK_pos = start  # расположение левого верхнего угла области отрисовки на поле
    enemies = set()
    while 1:
        FPS = clock.get_fps()
        pix_speed = (TILE_SIZE / (FPS if FPS != 0 else max_FPS)) * hero.speed
        pg.display.set_caption(str(int(hero.hp)))
        for event in pg.event.get():
            if event.type == pg.QUIT:
                exit()

            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_w:
                    # движение вверх
                    dirr[1] = -1
                elif event.key == pg.K_a:
                    # движение влево
                    dirr[0] = -1
                    hero.side = 'left'
                elif event.key == pg.K_d:
                    # движение вправо
                    dirr[0] = 1
                    hero.side = 'right'
                elif event.key == pg.K_s:
                    # движенияе вниз
                    dirr[1] = 1
                elif event.key == pg.K_k and not hero_attacked:
                    # атака героя
                    hero.hit(dirr)
                    pg.time.set_timer(26, 1000 // hero.attack_speed)
                    hero_attacked = True
                # отладка
                elif event.key == pg.K_m:
                    m = Unit(Map, (42, 42), (1, 1), 2, Unit_test_img, 0, 0, 0, 99, Unit_test_dead)
                    AI_Knight(Map, (32, 32), 1, Unit_test_img, 3, 0, 1, 10, Unit_test_dead, [hero], FPS)
                elif event.key == pg.K_n:
                    cnt = 0
                    for pos in bfs((33, 33), (41, 41), Map, [0, -11], 8):
                        print(pos)
                        cnt += 1
                        Unit(Map, pos, (1, 1), 2, f1.render(str(cnt), 1, BLACK), 0, 0, 0, 1, Unit_test_dead)
                elif event.key == pg.K_l:
                    Stone(hero.pos[0] - 1, hero.pos[1])

            elif event.type == pg.KEYUP:
                if event.key == pg.K_w:
                    # отмена движения вверх
                    dirr[1] = max(0, dirr[1])
                elif event.key == pg.K_a:
                    # отмена движения влево
                    dirr[0] = max(0, dirr[0])
                elif event.key == pg.K_d:
                    # отмена движения вправо
                    dirr[0] = min(0, dirr[0])
                elif event.key == pg.K_s:
                    # отмена движенияя вниз
                    dirr[1] = min(0, dirr[1])

            elif event.type == 24:
                hero_movable = True
                pg.time.set_timer(24, 0)

            elif event.type == 25:
                hero.tick()
                pg.time.set_timer(25, 0)

            elif event.type == 26:
                hero_attacked = False
                pg.time.set_timer(26, 0)

        # движение героя
        if hero_movable:
            if hero.move(dirr):
                pg.time.set_timer(24, 1000 // hero.speed)
                pg.time.set_timer(25, 1000 // (hero.speed * 2))
                hero_movable = False
            else:
                dirr = [0, 0]
            d_pix = [-dirr[0] * pix_speed, -dirr[1] * pix_speed]
            LK_pix = [(dirr[0] - 1) * TILE_SIZE, (dirr[1] - 1) * TILE_SIZE]
            LK_pos[0] += dirr[0]
            LK_pos[1] += dirr[1]

        # анимации
        objects = set()
        sc.fill(WHITE)
        LK_pix[0] += d_pix[0]
        LK_pix[1] += d_pix[1]
        LKP_int = [round(LK_pix[0]), round(LK_pix[1])]  # округлённые зачения положения в пикселях
        # 1. Отрисовка тайлов
        for dx in range(MS_visible_x):
            for dy in range(MS_visible_y):
                sc.blit(Map[LK_pos[0] + dx][LK_pos[1] + dy].get_BasicTile(LK_pos[0] + dx, LK_pos[1] + dy).img,
                        (LKP_int[0] + dx * TILE_SIZE, LKP_int[1] + dy * TILE_SIZE))
                if Map[LK_pos[0] + dx][LK_pos[1] + dy].code < 0 or Map[LK_pos[0] + dx][LK_pos[1] + dy].code == 2:
                    objects.add(Map[LK_pos[0] + dx][LK_pos[1] + dy])
                elif Map[LK_pos[0] + dx][LK_pos[1] + dy].code in enemy_codes and \
                        Map[LK_pos[0] + dx][LK_pos[1] + dy] not in enemies:
                    Map[LK_pos[0] + dx][LK_pos[1] + dy].cond = 'active'
                    enemies.add(Map[LK_pos[0] + dx][LK_pos[1] + dy])
        # 2. Отрисовка объектов
        for obj in objects:
            sc.blit(obj.img, calc_pix_pl(obj.pos, LK_pos, LKP_int))
        # 3. ИИ и перемещение противников
        for enemy in list(enemies):
            if enemy.cond != 'dead':
                enemy.update()
                enemy.draw(sc, calc_pix_pl(enemy.pos, LK_pos, LKP_int), TILE_SIZE)
            else:
                enemies.remove(enemy)
        # 4. Анимация героя
        if hero.hp <= 0:
            return
        hero.draw(sc, hero_pl)
        pg.display.update()
        clock.tick(max_FPS)

# загрузка и форматирование изображеий
clock = pg.time.Clock()
sc = pg.display.set_mode(((MS_visible_x - 2) * TILE_SIZE, (MS_visible_y - 2) * TILE_SIZE))  # окно
f1 = pg.font.SysFont('Arial', 36)
load = f1.render('Загрузка...', 1, WHITE)
load_pl = load.get_rect(center=(sc.get_width() // 2, sc.get_height() // 2))
sc.blit(load, load_pl)
pg.display.update()
GRASS_IMG1 = pg.transform.scale(pg.image.load(r'C:\Users\Тимофей\PycharmProjects\Sandbox\kolia_test\grass_1.png'), (TILE_SIZE, TILE_SIZE)).convert()
GRASS_IMG2 = pg.transform.scale(pg.image.load(r'C:\Users\Тимофей\PycharmProjects\Sandbox\kolia_test\grass_2.png'), (TILE_SIZE, TILE_SIZE)).convert()
GRASS_IMG3 = pg.transform.scale(pg.image.load(r'C:\Users\Тимофей\PycharmProjects\Sandbox\kolia_test\grass_3.png'), (TILE_SIZE, TILE_SIZE)).convert()
GRASS_IMG = [GRASS_IMG1, GRASS_IMG2, GRASS_IMG3]
ROCK_IMG = pg.transform.scale(pg.image.load(r'C:\Users\Тимофей\PycharmProjects\Sandbox\kolia_test\stone.png'), (TILE_SIZE, TILE_SIZE)).convert()
HERO_IMG_R = pg.transform.scale(pg.image.load('hero_test.png'), (TILE_SIZE * 2, TILE_SIZE * 2))  # TODO: выбор типа
HERO_IMG_L = pg.transform.flip(HERO_IMG_R, 1, 0)
HERO_RUN_R = pg.transform.scale(pg.image.load('hero_run_test.png'), (TILE_SIZE * 2, TILE_SIZE * 2))
HERO_RUN_L = pg.transform.flip(HERO_RUN_R, 1, 0)
HERO_ATTACK_R = pg.transform.scale(pg.image.load('hero_attack_test.png'), (TILE_SIZE * 2, TILE_SIZE * 2))
HERO_ATTACK_L = pg.transform.flip(HERO_ATTACK_R, 1, 0)
HERO_ANIMATIONS = {'run': {'left': HERO_RUN_L, 'right': HERO_RUN_R},
                   'stay': {'left': HERO_IMG_L, 'right': HERO_IMG_R},
                   'dead': HERO_IMG_R,
                   'attack': {'left': HERO_ATTACK_L, 'right': HERO_ATTACK_R}}  # TODO: hero img
Unit_test_img = pg.transform.scale(pg.image.load('unit_test.png'), (TILE_SIZE, TILE_SIZE))
Unit_test_dead = pg.transform.scale(pg.image.load('unit_dead_test.png'), (TILE_SIZE, TILE_SIZE))


single_player()
