from funcsions import *
import pygame as pg
import  random as rnd
pg.init()


# константы
Map_size_x, Map_size_y = 200, 100  # размеры карты X * Y
MS_visible_x, MS_visible_y = 42, 22
TILE_SIZE = 32
WHITE = (255, 255, 255)
BLACK = (1, 1, 1)
enemy_codes = [1]
friendly_codes = [101]
# конец констант


class BasicTile:
    def __init__(self, img):
        # img - изображения
        self.img = img
        self.code = 0

    def get_BasicTile(self, x, y):
        return self


class Object:
    def __init__(self, Map, pos, size, code, img):
        # pos - координаты левого верхнего угла (x, y)
        # size - размер (x, y)
        # code - код int
        # img - изображения
        self.Map = Map
        self.pos = pos
        self.size = size
        self.code = code
        self.img = img
        self.tile_landscape = [[None for i in range(self.size[1])] for j in range(self.size[0])]  # тайлы под изображением
        self.build()

    def get_BasicTile(self, x, y):
        return self.tile_landscape[x - self.pos[0]][y - self.pos[1]]

    def clear(self):
        # очистить объект с карты
        for i in range(self.size[0]):
            for j in range(self.size[1]):
                self.Map[self.pos[0] + i][self.pos[1] + j] = self.tile_landscape[i][j]

    def build(self):
        # разместить объект на поле (по координатам позиции pos)
        for i in range(self.size[0]):
            for j in range(self.size[1]):
                self.tile_landscape[i][j] = self.Map[self.pos[0] + i][self.pos[1] + j].get_BasicTile(self.pos[0] + i,self.pos[1] + j)
                self.Map[self.pos[0] + i][self.pos[1] + j] = self

    def set_place(self, x, y):
        # изменить место объекта
        self.clear()
        self.pos = (x, y)
        self.build()


class Unit(Object):
    def __init__(self, Map, pos, size, code, img, speed, damage, attack_speed, hp, dead_img):
        Object.__init__(self, Map, pos, size, code, img)
        self.speed = speed
        self.damage = damage
        self.hp = hp
        self.dead_img = dead_img
        self.attack_speed = attack_speed

    def attack(self, other):
        other.hp -= self.damage
        if other.hp <= 0:
            other.die()

    def die(self):
        # умирает и создёт на месте себя труп
        self.clear()
        Object(self.Map, self.pos, self.size, -11, self.dead_img)
        self.cond = 'dead'

class Hero(Unit):
    def __init__(self, Map, pos, size, code, speed, damage, attack_speed, hp, animations):
        self.prev_layer = [[None for i in range(size[1])] for j in range(size[0])]  # слой под героем
        Unit.__init__(self, Map, pos, size, code, animations['stay']['right'], speed, damage, attack_speed, hp, animations['dead'])
        self.moveable_codes = set([0, self.code])  # коды проходимых для героя объектов
        self.unfriendly_codes = set([1, 2])  # список кодов объектов, кторые герой может бить
        self.animations = animations
        self.cond = 'stay'
        self.side = 'right'
        self.animation_cnt = True

    def clear(self):
        # очистить объект с карты
        for i in range(self.size[0]):
            for j in range(self.size[1]):
                self.Map[self.pos[0] + i][self.pos[1] + j] = self.prev_layer[i][j]

    def build(self):
        # разместить объект на поле (по координатам позиции pos)
        for i in range(self.size[0]):
            for j in range(self.size[1]):
                self.tile_landscape[i][j] = self.Map[self.pos[0] + i][self.pos[1] + j].get_BasicTile(self.pos[0] + i,self.pos[1] + j)
                if self.Map[self.pos[0] + i][self.pos[1] + j].code <= 0:
                    self.prev_layer[i][j] = self.Map[self.pos[0] + i][self.pos[1] + j]
                self.Map[self.pos[0] + i][self.pos[1] + j] = self

    def move(self, dirr):
        if is_free(self.Map, (self.pos[0] + dirr[0], self.pos[1] + dirr[1]), self.size, self.moveable_codes):
            self.set_place(self.pos[0] + dirr[0], self.pos[1] + dirr[1])
            self.run(dirr)
            return True
        return False

    def draw(self, surf, pl):
        if self.cond == 'run':
            if self.animation_cnt:
                surf.blit(self.animations['run'][self.side], pl)
            else:
                surf.blit(self.animations['stay'][self.side], pl)
        elif self.cond != 'dead':
            surf.blit(self.animations[self.cond][self.side], pl)

    def tick(self):
        self.animation_cnt = not self.animation_cnt

    def set_side(self, dirr):
        if dirr[0] == 1:
            self.side = 'right'
        elif dirr[0] == -1:
            self.side = 'left'

    def run(self, dirr):
        if dirr == [0, 0]:
            self.cond = 'stay'
            return 0
        self.animation_cnt = True
        self.cond = 'run'
        self.set_side(dirr)

    def hit(self, dirr):
        self.set_side(dirr)
        self.cond = 'attack'
        enemies = set()
        if self.side == 'right':
            dx = self.size[0]
        else:
            dx = -1
        for dy in range(self.size[1]):
            if self.Map[self.pos[0] + dx][self.pos[1] + dy].code in self.unfriendly_codes:
                enemies.add(self.Map[self.pos[0] + dx][self.pos[1] + dy])
        for enemy in enemies:
            self.attack(enemy)


class AI_Knight(Unit):
    def __init__(self, Map, pos,code, img, speed, damage, attack_speed, hp, dead_img, targets, FPS):
        Unit.__init__(self, Map, pos, (1, 1), code, img, speed, damage, attack_speed, hp, dead_img)
        self.prev_pos = self.pos  # переменная для опредления направления движения во время прорисовки
        self.spetial_codes = [self.code]  # коды, при попадании на которые юниту позволено телепортироваться на соседние клетки
        self.moveable_codes = set([0, 11] + self.spetial_codes)  # коды проходимых объектов
        self.cond = 'inactive'
        self.FPS = FPS
        self.cnt = {'attack': 0, 'run': 0}
        self.targets = targets[:]
        self.target = targets[-1]
        self.path = deque(update_path(self, self.pos, self.target.pos, self.moveable_codes, self.Map))
        if len(self.path) < 2:
            self.path.extend(update_path(self, self.path[0], self.target.pos, self.moveable_codes, self.Map))

    def move(self, target_pl):
        self.prev_pos = self.pos
        if self.Map[self.path[0][0]][self.path[0][1]].code not in self.moveable_codes:
            self.path = deque(update_path(self, self.pos, target_pl, self.moveable_codes, self.Map))
        if self.Map[self.path[0][0]][self.path[0][1]].code in self.spetial_codes:
            r1 = [-1, 1]
            r2 = [-1, 1]
            rnd.shuffle(r1)
            rnd.shuffle(r2)
            for dx in r1 + [0]:
                for dy in r2 + [0]:
                    if self.Map[self.path[0][0] + dx][self.path[0][1] + dy] in self.moveable_codes:
                        self.path.popleft()
                        self.path.appendleft((self.path[0][0] + dx, self.path[0][1] + dy))
        self.set_place(self.path[0][0], self.path[0][1])
        self.path.popleft()
        if len(self.path) == 0:
            self.path.extend(update_path(self, self.pos, target_pl, self.moveable_codes, self.Map))
        if len(self.path) == 1:
            self.path.extend(update_path(self, self.path[0], target_pl, self.moveable_codes, self.Map))

    def find_target(self):
        pass

    def update(self):
        for key in self.cnt.keys():
            self.cnt[key] -= 1
        if self.cond == 'inactive':
            return
        if self.cnt['attack'] <= 0:
            for dx in [-1, 1]:
                if self.Map[self.pos[0] + dx][self.pos[1]].code in friendly_codes:
                    self.attack(self.Map[self.pos[0] + dx][self.pos[1]])
                    self.cnt['attack'] = self.FPS / self.attack_speed
                    return
        if self.cnt['run'] <= 0 and self.target is not None and dist(self.pos, self.target.pos) >= 2:
            self.move(self.target.pos)
            self.cnt['run'] = self.FPS / self.speed
            self.cnt['attack'] = max(self.FPS / self.speed, self.cnt['attack'])


    def draw(self, surf, relative_pos, TILE_SIZE):
        # relative_pos - координаты левого верхего угла тайла, в который юнит движется (в пикселях от края экрана)
        if self.cnt['run'] >= 0:
            pix_dist = int((TILE_SIZE / self.FPS) * self.speed * self.cnt['run'])
            surf.blit(self.img, (relative_pos[0] - (self.pos[0] - self.prev_pos[0]) * pix_dist,
                                 relative_pos[1] - (self.pos[1] - self.prev_pos[1]) * pix_dist))
        else:
            surf.blit(self.img, relative_pos)






def calc_pix_pl(pos, LK_pos, LK_pix):
    # расчёт положения отрисовки в пикселях для статичных объектов
    return (pos[0] - LK_pos[0]) * TILE_SIZE + LK_pix[0], (pos[1] - LK_pos[1]) * TILE_SIZE + LK_pix[1]


def is_free(Map, pl, size, elem):
    # проверка на то, что во всей области нет препятствий
    res = True
    for i in range(size[0]):
        for j in range(size[1]):
            try:
                res = res and Map[pl[0] + i][pl[1] + j].code in elem
            except IndexError:
                res = False
    return res
