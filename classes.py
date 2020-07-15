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
        self.prev_layer = [[None for i in range(size[1])] for j in range(size[0])]  # слой под героем
        self.tile_landscape = [[None for i in range(self.size[1])] for j in range(self.size[0])]  # тайлы под изображением
        self.build()

    def get_BasicTile(self, x, y):
        return self.tile_landscape[x - self.pos[0]][y - self.pos[1]]

    def clear(self):
        # очистить объект с карты
        for i in range(self.size[0]):
            for j in range(self.size[1]):
                self.Map[self.pos[0] + i][self.pos[1] + j] = self.prev_layer[i][j]

    def build(self):
        # разместить объект на поле (по координатам позиции pos)
        for i in range(self.size[0]):
            for j in range(self.size[1]):
                self.tile_landscape[i][j] = self.Map[self.pos[0] + i][self.pos[1] + j].get_BasicTile(self.pos[0] + i,
                                                                                                     self.pos[1] + j)
                self.prev_layer[i][j] = self.Map[self.pos[0] + i][self.pos[1] + j].get_BasicTile(self.pos[0] + i,
                                                                                                 self.pos[1] + j)
                if self.Map[self.pos[0] + i][self.pos[1] + j].code <= 0:
                    self.prev_layer[i][j] = self.Map[self.pos[0] + i][self.pos[1] + j]
                self.Map[self.pos[0] + i][self.pos[1] + j] = self

    def set_place(self, x, y):
        # изменить место объекта
        self.clear()
        self.pos = (x, y)
        self.build()


class Hero(Object):
    def __init__(self, Map, pos, size, code, speed, damage, attack_speed, hp, animations):
        Object.__init__(self, Map, pos, size, code, animations['stay']['right'])
        self.speed = speed
        self.damage = damage
        self.hp = hp
        self.max_hp = hp
        self.attack_speed = attack_speed
        self.movable_codes = {0, self.code, -11, 3}  # коды проходимых для героя объектов
        self.animations = animations
        self.cond = 'stay'
        self.side = 'right'
        self.animation_cnt = True
        # список свободных мест вокруг героя
        self.foe = set()

    def attack(self, other):
        other.hp -= self.damage
        if other.hp <= 0:
            other.die()

    def move(self, dirr):
        if is_free(self.Map, (self.pos[0] + dirr[0], self.pos[1] + dirr[1]), self.size, self.movable_codes):
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
            if self.Map[self.pos[0] + dx][self.pos[1] + dy].code > 1000:
                enemies.add(self.Map[self.pos[0] + dx][self.pos[1] + dy])
        for enemy in enemies:
            self.attack(enemy)

    def die(self):
        raise SystemExit  # TODO: hero.die


class Unit_AI(Object):
    def __init__(self, Map, pos, code, img, speed, damage, attack_speed, hp, dead_img, targets, FPS):
        # ---------- параметры ----------
        Object.__init__(self, Map, pos, (1, 1), code, img)
        self.speed = speed
        self.damage = damage
        self.hp = hp
        self.max_hp = hp
        self.dead_img = dead_img
        self.attack_speed = attack_speed
        # ---------- вспомогательные переменные ----------
        self.prev_pos = self.pos  # переменная для опредления направления движения во время прорисовки
        self.special_codes = []  # коды, при попадании на которые юниту позволено телепортироваться на соседние клетки
        self.movable_codes = set([0, -11] + self.special_codes)  # коды проходимых объектов
        self.cond = 'inactive'
        self.FPS = FPS
        self.cnt = {'attack': 0, 'run': 0, 'target': 0}
        # ---------- переменные для движения ----------
        # список свободных мест вокруг юнита
        self.foe = set()
        self.targets = targets[:]
        self.rel_target_pos = None
        self.target = None
        self.find_target()
        self.path = deque(update_path(self, self.pos, self.target.pos, self.movable_codes, self.Map))
        if len(self.path) < 2:
            self.path.extend(update_path(self, self.path[0], self.target.pos, self.movable_codes, self.Map))

    def attack(self, other):
        other.hp -= self.damage
        if other.hp <= 0:
            other.die()

    def die(self):
        # умирает и создёт на месте себя труп
        self.clear()
        Object(self.Map, self.pos, self.size, -11, self.dead_img)
        self.cond = 'dead'
        if self.target is not None and self.target is not self:
            self.target.foe.remove(self.rel_target_pos)

    def update_targets(self, targets):
        self.targets = targets

    def move(self, target_pl):
        self.prev_pos = self.pos
        if self.Map[self.path[0][0]][self.path[0][1]].code not in self.movable_codes:
            self.path = deque(update_path(self, self.pos, target_pl, self.movable_codes, self.Map))
        if self.Map[self.path[0][0]][self.path[0][1]].code in self.special_codes:
            r1 = [-1, 1]
            r2 = [-1, 1]
            rnd.shuffle(r1)
            rnd.shuffle(r2)
            for dx in r1 + [0]:
                for dy in r2 + [0]:
                    if self.Map[self.path[0][0] + dx][self.path[0][1] + dy] in self.movable_codes:
                        self.path.popleft()
                        self.path.appendleft((self.path[0][0] + dx, self.path[0][1] + dy))
        self.set_place(self.path[0][0], self.path[0][1])
        self.path.popleft()
        if len(self.path) == 0:
            self.path.extend(update_path(self, self.pos, target_pl, self.movable_codes, self.Map))
        if len(self.path) == 1:
            self.path.extend(update_path(self, self.path[0], target_pl, self.movable_codes, self.Map))

    def find_target(self):
        # переопределить в производном классе
        if self.target is not None and self.target is not self:
            self.target.foe.remove(self.rel_target_pos)
        for target in self.targets:
            for pos in [(dx, dy) for dx in [target.size[0], -1] for dy in range(target.size[1])]:
                if pos not in target.foe:
                    target.foe.add(pos)
                    self.rel_target_pos = pos
                    self.target = target
                    self.cnt['target'] = self.FPS * self.speed * 4
                    return
        self.rel_target_pos = (rnd.randint(-1, 1), rnd.randint(-1, 1))
        self.target = self
        self.cnt['target'] = self.FPS * self.speed

    def hit(self):
        # переопределить в производном классе
        for dx in [-1, 1]:
            if self.Map[self.pos[0] + dx][self.pos[1]] in self.targets:
                self.attack(self.Map[self.pos[0] + dx][self.pos[1]])
                self.cnt['attack'] = self.FPS / self.attack_speed
                return

    def update(self):
        for key in self.cnt.keys():
            self.cnt[key] -= 1
        if self.cond == 'inactive':
            return
        if self.cnt['attack'] <= 0:
            self.hit()
        if self.target is None or self.target.cond == 'dead' or self.cnt['target'] <= 0:
            self.find_target()
        if self.cnt['run'] <= 0:
            self.move((self.target.pos[0] + self.rel_target_pos[0], self.target.pos[1] + self.rel_target_pos[1]))
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


class FriendlyKnight(Unit_AI):
    def __init__(self, Map, pos, img, ch, targets, hero, FPS, friendly_list):
        friendly_list.append(self)
        self.hero = hero
        self.movable_codes = {3, 0, -11}
        self.ch = ch
        self.ch['img'] = img['stay']
        Unit_AI.__init__(self, Map, pos, 3, 1, 1, 1, 1, ch['hp']['attack'], img['dead'], targets, FPS)
        self.set_condition('attack')

    def set_condition(self, condition):
        if condition == 'other' and self.cond == 'attack':
            condition = 'defence'
        if condition == 'other' and self.cond == 'defence':
            condition = 'attack'
        # необходимо передать 'attack' или 'defence'
        self.cond = condition
        self.attack_speed = self.ch['attack_speed'][condition]
        self.speed = self.ch['speed'][condition]
        self.img = self.ch['img'][condition]
        self.damage = self.ch['damage'][condition]
        self.hp *= self.ch['hp'][condition] / self.max_hp
        self.max_hp = self.ch['hp'][condition]


    def find_target(self):
        if self.target is not None and self.target is not self:
            self.target.foe.remove(self.rel_target_pos)
        if self.cond == 'attack':
            for target in sorted(self.targets, key=lambda t: (dist(t.pos, self.hero.pos), t.hp)):
                for pos in sorted([(dx, dy) for dx in [target.size[0], -1] for dy in range(target.size[1])],
                                  key=lambda t: dist(self.pos, (t[0] + target.pos[0], t[1] + target.pos[1]))):
                    if pos not in target.foe:
                        target.foe.add(pos)
                        self.rel_target_pos = pos
                        self.target = target
                        self.cnt['target'] = self.FPS / self.speed * 4
                        return
        # если таких позиций нет или состояние - защита:
        d = 1
        while 1:
            a = sorted([(dx, dy) for dx in [self.hero.size[0] + d, -1 - d] for dy in range(-(d // 2), self.hero.size[1] + (d // 2))],
                       key=lambda t: dist(self.pos, (t[0] + self.hero.pos[0], t[1] + self.hero.pos[1])))
            for pos in a:
                if pos not in self.hero.foe:
                    self.hero.foe.add(pos)
                    self.rel_target_pos = pos
                    self.target = self.hero
                    self.cnt['target'] = self.FPS / self.speed * 2
                    return
            d += 2


class UnfriendlyKnight(Unit_AI):
    def __init__(self, Map, pos, img, ch, targets, FPS):
        Unit_AI.__init__(self, Map, pos, 1004, img['stay'], ch['speed'], ch['damage'], ch['attack_speed'], ch['hp'], img['dead'], targets, FPS)

    def find_target(self):
        if self.target is not None and self.target is not self:
            self.target.foe.remove(self.rel_target_pos)
        d = 0
        while 1:
            for target in sorted(self.targets, key=lambda t: (dist(t.pos, self.pos), t.hp)):
                for pos in sorted([(dx, dy) for dx in [target.size[0] + d, -1 - d] for dy in range(-d, target.size[1] + d)],
                                  key=lambda t: dist(self.pos, (t[0] + target.pos[0], t[1] + target.pos[1]))):
                    if pos not in target.foe:
                        target.foe.add(pos)
                        self.rel_target_pos = pos
                        self.target = target
                        self.cnt['target'] = self.FPS / self.speed * 3
                        return
            d += 1


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
