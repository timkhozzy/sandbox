from math import inf
from collections import deque


# объявление сторонних функций
def lin2(d1, d2):
    # прямая, проходящая через 2 заданные точки
    x1, y1 = d1
    x2, y2 = d2
    return lambda x: ((y1 - y2) * x + x1 * y2 - x2 * y1) / (x1 - x2)


def arrow(st, fn):
    # переделывает прямую в "змейку" от st до fn
    x, y = st
    if x == fn[0]:
        res = []
        for i in range(min(y, fn[1]), max(y, fn[1])):
            res += [(x, i)]
        return res + [fn]
    elif y == fn[1]:
        res = []
        for i in range(min(x, fn[0]), max(x, fn[0])):
            res += [(i, y)]
        return res + [fn]
    else:
        x = st[0]
        y = st[1]
        res = []
        x_w = -1 if fn[0] - x < 0 else 1  # полуплоскость по x
        y_w = -1 if fn[1] - y < 0 else 1  # по y
        lin_x = lin2(fn, st)
        lin_y = lin2(fn[::-1], st[::-1])
        while (x, y) != fn:
            # двигаемся от % к @
            dirr = [0, 0]
            """
            ###
            @%@
            ###
            """
            if y - 0.5 <= lin_x(x + 0.5) <= y + 0.5:
                dirr[0] += 1

            """
            #@#
            #%#
            #@#
            """
            if x - 0.5 <= lin_y(y + 0.5) <= x + 0.5:
                dirr[1] += 1

            res += [(x, y)]
            x += dirr[0] * x_w
            y += dirr[1] * y_w
        return res + [(x, y)]


def dist(coords1, coords2):
    # расстояние между двумя точками
    return max(abs(coords1[0] - coords2[0]), abs(coords1[1] - coords2[1]))


def bfs(start, finish, Map, movable_codes, dist):
    cur_map = []
    for x in range(min(start[0], finish[0]) - dist, max(start[0], finish[0]) + dist):
        line = []
        for y in range(min(start[1], finish[1]) - dist, max(start[1], finish[1]) + dist):
            line.append([Map[x][y].code in movable_codes, inf])
        cur_map.append(line)
    lk = (min(start[0], finish[0]) - dist, min(start[1], finish[1]) - dist)
    queue = deque([(start[0] - lk[0], start[1] - lk[1])])
    st = queue[0]
    cur_map[queue[0][0]][queue[0][1]] = [False, 1]
    fn = (finish[0] - lk[0], finish[1] - lk[1])
    if cur_map[fn[0]][fn[1]] == inf:
        return [start]
    while len(queue) > 0 and cur_map[fn[0]][fn[1]]:
        now = queue.popleft()
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if len(cur_map) > now[0] + dx >= 0 and len(cur_map[0]) > now[1] + dy >= 0 and cur_map[now[0] + dx][now[1] + dy][0]:
                    cur_map[now[0] + dx][now[1] + dy] = [False, cur_map[now[0]][now[1]][1] + 1]
                    queue.append((now[0] + dx, now[1] + dy))
    # print('\n'.join(map(lambda m: ' '.join(map(lambda b: str(b[1]), m)), cur_map)))
    path = []
    now = fn
    cnt = 0
    while now != st and cnt < 10 ** 6:
        cnt += 1
        path.append((now[0] + lk[0], now[1] + lk[1]))
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                try:
                    if cur_map[now[0] + dx][now[1] + dy][1] == cur_map[now[0]][now[1]][1] - 1:
                        now = (now[0] + dx, now[1] + dy)
                        break
                except IndexError:
                    pass
            else:
                continue
            break
        if path[-1] == (now[0] + lk[0], now[1] + lk[1]):
            return [start]
    if cnt == 10 ** 6:
        return [start]
    return path[::-1]


def update_path(self, start, target_pl, movable_codes, Map):
    if start == target_pl:
        return [start]
    # поиск пути у компьютерных соеников
    x_w = -1 if target_pl[0] < start[0] else 1  # полуплоскость по x
    y_w = -1 if target_pl[1] < start[1] else 1  # по y
    lin_y = (lambda x: inf) if target_pl[0] == start[0] else lin2(target_pl, start)
    lin_x = (lambda y: inf) if target_pl[1] == start[1] else lin2(target_pl[::-1], start[::-1])
    x, y = start
    dirr = [0, 0]
    if y - 0.5 <= lin_y(x + 0.5) <= y + 0.5:
        # x side
        dirr[0] += x_w
    if x - 0.5 <= lin_x(y + 0.5) <= x + 0.5:
        # y side
        dirr[1] += y_w
    next = (start[0] + dirr[0], start[1] + dirr[1])

    if Map[next[0]][next[1]].code in movable_codes:
        return [next]
    else:
        now = next
        cnt = 0  # чтоб за грануцу карты не улетал
        while Map[now[0]][now[1]].code not in movable_codes and now != target_pl:
            lin_y = (lambda x: inf) if target_pl[0] == now[0] else lin2(target_pl, now)
            lin_x = (lambda y: inf) if target_pl[1] == now[1] else lin2(target_pl[::-1], now[::-1])
            x, y = now
            dirr = [0, 0]
            if y - 0.5 <= lin_y(x + 0.5) <= y + 0.5:
                # x side
                dirr[0] = x_w
            if x - 0.5 <= lin_x(y + 0.5) <= x + 0.5:
                # y side
                dirr[1] = y_w
            now = (now[0] + dirr[0], now[1] + dirr[1])
            cnt += 1
        d = 3
        path = bfs(start, now, Map, movable_codes, d)
        while path == [start] and d < 10:
            d += 2
            path = bfs(start, now, Map, movable_codes, d)
    return path
