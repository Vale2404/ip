from vepar import *
from lifeparser import *
import os
import time


def _dimenzije(dijagonale):
    D = len(dijagonale) # broj dijagonala
    R = max(len(d) for d in dijagonale) # duljina najduze dijagonale
    C = D - R + 1
    return R, C


def u_matricu(dijagonale):
    R, C = _dimenzije(dijagonale)
    matrica = [[None] * C for _ in range(R)] # prazna matrica dim 11*19
    for d, dijagonala in enumerate(dijagonale): # d je index dijagonale, dijagonala je lista vrijednosti
        # od kojeg retka krece ova dijagonala?
        i_min = max(0, d - C + 1)
        
        for r, vrijednost in enumerate(dijagonala):
            # r je index unutar dijagonale, vrijednost je vrijednost na toj poziciji
            matrica[i_min + r][d - i_min - r] = vrijednost
    return matrica, R, C


def u_dijagonale(matrica, R, C):
    dijagonale = []
    for d in range(R + C - 1):
        i_min = max(0, d - C + 1)
        i_max = min(d, R - 1)
        dijagonale.append([matrica[i][d - i] for i in range(i_min, i_max + 1)])
    return dijagonale


ZIVA = "\u2b1b"
MRTVA = "\u2b1c"


def ispisi(dijagonale):
    matrica, _, _ = u_matricu(dijagonale)
    for redak in matrica:
        print(''.join(ZIVA if element.sadržaj == 'Ž' else MRTVA for element in redak))


def _zivo(element):
    return element ^ T.STANICA and element.sadržaj == 'Ž' 


def tick(dijagonale):
    R, C = _dimenzije(dijagonale)
    matrica, _, _ = u_matricu(dijagonale)
    zivo = [[_zivo(matrica[i][j]) for j in range(C)] for i in range(R)]
    nova_matrica = [[0] * C for _ in range(R)]
    for i in range(R):
        for j in range(C):
            zivi_susjedi = 0
            for di in [-1, 0, 1]:
                for dj in [-1, 0, 1]:
                    if di == 0 and dj == 0:
                        continue
                    ni, nj = i + di, j + dj
                    if 0 <= ni < R and 0 <= nj < C and zivo[ni][nj]:
                        zivi_susjedi += 1
            
            if zivo[i][j]:
                if zivi_susjedi == 2 or zivi_susjedi == 3:
                    nova_matrica[i][j] = Token(T.STANICA, 'Ž')
                else: nova_matrica[i][j] = Token(T.STANICA, 'M')
            else: 
                if zivi_susjedi == 3:
                    nova_matrica[i][j] = Token(T.STANICA, 'Ž')
                else:
                    nova_matrica[i][j] = Token(T.STANICA, 'M')

    return u_dijagonale(nova_matrica, R, C)


matrica = P(ulaz)

for korak in range(10):
    os.system('cls' if os.name == 'nt' else 'clear')
    print('Generacija {}:'.format(korak))
    ispisi(matrica)
    time.sleep(1)
    matrica = tick(matrica)