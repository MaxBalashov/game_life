import numpy as np


def prob_scaling(*prob_arrays):

    p_sum = sum(prob_arrays)
    
    if p_sum == 1:
        return prob_arrays
    else:
        return [p_arr / p_sum for p_arr in prob_arrays]

    
def init_ocean(n=50, m=50, scale=True, random_seed=None, *prob_arrays):
    
    # шкалирование, если вероятности в сумме != 1
    if scale:
        prob_arrays = prob_scaling(*prob_arrays)
    
    # для детерменированной инициализации
    np.random.seed(seed=random_seed)
    
    # генерация матрицы океана с размерами (n, m)
    ocean = np.random.choice(
        range(len(prob_arrays)),
        size=(n, m),
        p = list(prob_arrays)
    )
    return ocean


def get_neighbors_coo(i, j, ocean):
    
    n, m = ocean.shape
    
    # верхняя строка
    if i == 0:
        if j == 0: # верхний левый угол
            return (0, 1, 1), (1, 0, 1)
        elif j == m-1: # верхний правый угол
            return (0, 1, 1), (m-2, m-2, m-1)
        else: # верхняя строка без углов
            return (0, 0, 1, 1, 1), (j-1, j+1, j-1, j, j+1)
    # нижняя строка
    elif i == n-1:
        if j == 0: # нижний левый угол
            return (n-2, n-2, n-1), (0, 1, 1)
        elif j == m-1: # нижний правый угол
            return (n-2, n-2, n-1), (m-2, m-1, m-2)
        else: # нижняя строка без углов
            return (n-2, n-2, n-2, n-1, n-1), (j-1, j, j+1, j-1, j+1)
    # левая строка без углов
    elif j == 0:
        return (i-1, i-1, i, i+1, i+1), (0, 1, 1, 0, 1)
    # правая строка без углов
    elif j == m-1:
        return (i-1, i-1, i, i+1, i+1), (m-2, m-1, m-2, m-2, m-1)
    # неграничные части
    else:
        return (i-1, i-1, i-1, i, i, i+1, i+1, i+1), (j-1, j, j+1, j-1, j+1, j-1, j, j+1)

    
def get_neighbors(i, j, ocean):
    neighbors = ocean[
        tuple(get_neighbors_coo(i=i, j=j, ocean=ocean))
    ]
    return neighbors


def is_under_over_population(neighbors, kind, low=2, high=4):
    '''
    Comfortable existence for instance of some kind
    when number of neighbors of same kind is in [low, high) = {low, low+1, ..., high-1}.
    '''
    neighbors_of_same_kind = np.count_nonzero(neighbors == kind)
    return (neighbors_of_same_kind < low) | (neighbors_of_same_kind >= high)


def step_ocean(ocean):
    # предыдущее состояние океана
    ocean_prev = np.copy(ocean)

    # координаты пустоты, рыб, креветок
    coo_empty_i, coo_empty_j = np.where(ocean_prev == 0)
    coo_fish_i, coo_fish_j = np.where(ocean_prev == 2)
    coo_shrimp_i, coo_shrimp_j = np.where(ocean_prev == 3)

    # пустые места
    for i, j in zip(coo_empty_i, coo_empty_j):
        neighbors = get_neighbors(i, j, ocean_prev)
        if np.count_nonzero(neighbors == 2) == 3:
            ocean[i, j] = 2 # если ровно 3 рыбы
        elif np.count_nonzero(neighbors == 3) == 3:
            ocean[i, j] = 3 # если ровно 3 креветки

    # рыбы
    for i, j in zip(coo_fish_i, coo_fish_j):
        neighbors = get_neighbors(i, j, ocean_prev)
        # много или мало соседей своего вида
        if is_under_over_population(neighbors, kind=2):
            ocean[i, j] = 0

    # креветки
    for i, j in zip(coo_shrimp_i, coo_shrimp_j):
        neighbors = get_neighbors(i, j, ocean_prev)
        # много или мало соседей своего вида
        if is_under_over_population(neighbors, kind=3):
            ocean[i, j] = 0
            
    return ocean


if __name__ == '__main__':

    import curses
    import sys
    from time import sleep
    
    # гиперпараметры
    ## вывод всех элементов массива 
    np.set_printoptions(threshold=np.inf)
    ## размер океана
    n, m = 20, 20
    ## вероятности
    p_fish = 0.25
    p_shrimp = 0.25
    p_rock = 0.15
    p_empty = 0.35
    ## зерно случ генератора
    random_seed = None
    ## шкалирование
    scale = True
    
    # случайная инициализация океана
    ocean = init_ocean(n, m, scale, random_seed, p_empty, p_rock, p_fish, p_shrimp)

    # вывод в консоль
    # https://stackoverflow.com/questions/6840420/python-rewrite-multiple-lines-in-the-console
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    
    cnt = 1
    try:
        while True:
            stdscr.addstr(0, 0, 'Notation: empty=0, rock=1, fish=2, shrimp=3')
            stdscr.addstr(1, 0, 'Number of ocean epoch: {}'.format(cnt))
            stdscr.addstr(2, 0, np.array2string(ocean))
            stdscr.refresh()
            sleep(1)
            ocean_prev = np.copy(ocean)
            ocean = step_ocean(ocean)
            cnt += 1
            # если океан стационарен, то конец цикла
            if np.array_equal(ocean_prev, ocean):
                stdscr.addstr(n + 2, 0, 'Ocean is fixed!')
                for i in range(5):
                    stdscr.addstr(n + 3, 0, 'Application quits in next 5 seconds: {}'.format(i+1))
                    stdscr.refresh()
                    sleep(1)
                break
    finally:
        curses.echo()
        curses.nocbreak()
        curses.endwin()