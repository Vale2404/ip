"""Istinitosna vrijednost, i jednostavna optimizacija, formula logike sudova.

Standardna definicija iz [Vuković, Matematička logika]:
* Propozicijska varijabla (P0, P1, P2, ..., P9, P10, P11, ....) je formula
* Ako je F formula, tada je i !F formula (negacija)
* Ako su F i G formule, tada su i (F&G), (F|G), (F->G) i (F<->G) formule
Sve zagrade (oko binarnih veznika) su obavezne!

Interpretaciju zadajemo imenovanim argumentima: vrijednost(F, P2=True, P7=False)
Optimizacija (formula.optim()) zamjenjuje potformule oblika !!F sa F."""


from vepar import *


subskript = str.maketrans('0123456789', '₀₁₂₃₄₅₆₇₈₉')

class T(TipoviTokena):
    NEG, KONJ, DISJ, OTV, ZATV = '!&|()'
    KOND, BIKOND = '->', '<->'
    class PVAR(Token):  # P0, P1, P2, ... P153, ...
        def vrijednost(var, I): return I[var]
        def makni_neg(var): return var, True
        def ispis(var): return var.sadržaj.translate(subskript)


@lexer
def ls(lex):
    for znak in lex:
        match znak:
            case 'P':
                prvo = next(lex)
                if not prvo.isdecimal(): raise lex.greška('očekivana znamenka')
                if prvo != '0': lex * str.isdecimal
                yield lex.token(T.PVAR)
            case '-':
                lex >> '>'
                yield lex.token(T.KOND)
            case '<':
                lex >> '-'
                lex >> '>'
                yield lex.token(T.BIKOND)
            case _: yield lex.literal(T)


### Beskontekstna gramatika:
# formula -> NEG formula | PVAR | OTV formula binvez formula ZATV
# binvez -> KONJ | DISJ | KOND | BIKOND

### Apstraktna sintaksna stabla (i njihovi atributi):
# formula: PVAR: Token
#          Negacija: ispod:formula
#          Binarna: veznik:T lijevo:formula desno:formula


class P(Parser):
    def formula(p) -> 'PVAR|Negacija|Konjunkcija|Disjunkcija|Kondicional|Bikondicional':
        if varijabla := p >= T.PVAR: return varijabla
        elif p >= T.NEG: 
            ispod = p.formula()
            return Negacija(ispod)
        elif p >> T.OTV:
            lijevo = p.formula()
            klasa = p.binvez()
            desno = p.formula()
            p >> T.ZATV
            return klasa(lijevo, desno)

    def binvez(p): 
        if p >= T.KONJ: return Konjunkcija
        elif p >= T.DISJ: return Disjunkcija
        elif p >= T.KOND: return Kondicional
        elif p >= T.BIKOND: return Bikondicional
        else: raise p.greška()


class Negacija(AST):
    ispod: P.formula
    veznik = '¬'

    def vrijednost(negacija, I): return not negacija.ispod.vrijednost(I)

    def makni_neg(negacija):
        bez_neg, pozitivna = negacija.ispod.makni_neg()
        return bez_neg, not pozitivna

    def ispis(negacija): return negacija.veznik + negacija.ispod.ispis()


class Binarna(AST):
    lijevo: P.formula
    desno: P.formula

    def vrijednost(self, I):
        klasa = type(self)
        l = self.lijevo.vrijednost(I)
        d = self.desno.vrijednost(I)
        return klasa.tablica(l, d)

    def makni_neg(self):
        klasa = type(self)
        lijevo, lijevo_poz = self.lijevo.makni_neg()
        desno, desno_poz = self.desno.makni_neg()
        return klasa.xform(lijevo, desno, lijevo_poz, desno_poz), klasa.tablica(lijevo_poz, desno_poz)

    def ispis(self):
        return '(' + self.lijevo.ispis() + self.veznik + self.desno.ispis() + ')'


class Disjunkcija(Binarna):
    veznik = '∨'

    def tablica(l, d): return l or d

    def xform(lijevo, desno, lijevo_poz, desno_poz):
        match lijevo_poz, desno_poz:
            case True, True: return Disjunkcija(lijevo, desno)
            case False, True: return Kondicional(lijevo, desno)
            case True, False: return Kondicional(desno, lijevo)
            case False, False: return Konjunkcija(lijevo, desno)
            case _: assert False, 'nepokriveni slučaj!'


class Konjunkcija(Binarna):
    veznik = '∧'

    def tablica(l, d): return l and d

    def xform(lijevo, desno, lijevo_poz, desno_poz):
        return Disjunkcija.xform(lijevo, desno, not lijevo_poz, not desno_poz)
    

class Kondicional(Binarna):
    veznik = '→'

    def tablica(l, d):
        if l: return d
        return True

    def xform(lijevo, desno, lijevo_poz, desno_poz):
        return Disjunkcija.xform(lijevo, desno, not lijevo_poz, not desno_poz)


class Bikondicional(Binarna):
    veznik = '↔'

    def tablica(l, d): return l == d

    def xform(lijevo, desno, lijevo_poz, desno_poz):
        return Bikondicional(lijevo, desno)


def optim(formula):
    """Pretvara formulu (AST) u oblik s najviše jednom negacijom."""
    bez_neg, pozitivna = formula.makni_neg()
    if pozitivna: return bez_neg
    else: return Negacija(bez_neg)


def istinitost(formula, **interpretacija):
    I = Memorija(interpretacija)
    return formula.vrijednost(I)


for ulaz in '!(P5&!!(P0|!P3))', '(!P0&(!P1<->!P5))':
    ls(ulaz)
    prikaz(F := P(ulaz))
    print(F.ispis())
    prikaz(F := optim(F))
    print(F.ispis())
    print(f'{istinitost(F, P0=False, P3=True, P5=False,  P1=True)=}')
    print('-' * 60)

for krivo in 'P', 'P00', 'P1\tP2', 'P34<>P56':
    with LeksičkaGreška: ls(krivo)


# DZ: implementirajte još neke optimizacije: npr. F|!G u G->F. Rijeseno!
# DZ: Napravite totalnu optimizaciju negacije: svaka formula s najviše jednim !. Rijeseno!
# ~~  *Za ovo bi vjerojatno bilo puno lakše imati po jedno AST za svaki veznik.