"""Interpreter za jednostavni fragment jezika C++: petlje, grananja, ispis.
    Prema zadatku s kolokvija 16. veljače 2015. (Puljić).
    * petlje: for(var = broj; var < broj; var ++ ili var += broj) naredba
    * grananja: if(var == broj) naredba
    * ispis: cout << var1 << var2 << ..., s opcionalnim << endl na kraju

Tijelo petlje može biti i blok u vitičastim zagradama.
Podržana je i naredba break za izlaz iz unutarnje petlje:
    nelokalna kontrola toka realizirana je pomoću izuzetka Prekid."""


from vepar import *
from typing import Optional


class T(TipoviTokena):
    FOR, COUT, ENDL, IF = 'for', 'cout', 'endl', 'if'
    OOTV, OZATV, VOTV, VZATV, MANJE, JEDNAKO, TOČKAZ = '(){}<=;'
    PLUSP, PLUSJ, MMANJE, JJEDNAKO = '++', '+=', '<<', '=='
    class BREAK(Token):
        literal = 'break'
        def izvrši(self): raise Prekid
    class CONTINUE(Token):
        literal = 'continue'
        def izvrši(self): raise Nastavi
    class BROJ(Token):
        def vrijednost(self): return int(self.sadržaj)
    class IME(Token):
        def vrijednost(self): return rt.mem[self]
    class INT(Token):
        literal = 'int'

@lexer
def cpp(lex):
    for znak in lex:
        if znak.isspace(): lex.zanemari()
        elif znak == '+':
            if lex >= '+': yield lex.token(T.PLUSP)
            elif lex >= '=': yield lex.token(T.PLUSJ)
            else: raise lex.greška('u ovom jeziku nema samostalnog +')
        elif znak == '<': yield lex.token(T.MMANJE if lex >= '<' else T.MANJE)
        elif znak == '=':
            yield lex.token(T.JJEDNAKO if lex >= '=' else T.JEDNAKO)
        elif znak.isalpha() or znak == '_':
            lex * {str.isalnum, '_'}
            yield lex.literal_ili(T.IME)
        elif znak.isdecimal():
            lex.prirodni_broj(znak)
            yield lex.token(T.BROJ)
        else: yield lex.literal(T)


## Beskontekstna gramatika
# start -> naredbe naredba
# naredbe -> '' | naredbe naredba
# naredba -> deklaracija | petlja | grananje | ispis TOČKAZ | BREAK TOČKAZ | CONTINUE TOČKAZ | PraznaNaredba | blok
# deklaracija -> INT IME TOČKAZ
# blok -> VOTV naredbe VZATV
# for -> FOR OOTV IME# JEDNAKO BROJ TOČKAZ IME# MANJE BROJ TOČKAZ
# 	     IME# inkrement OZATV
# petlja -> for naredba | for VOTV naredbe VZATV
# inkrement -> PLUSP | PLUSJ BROJ
# ispis -> COUT varijable | COUT varijable MMANJE ENDL
# varijable -> '' | varijable MMANJE IME
# grananje -> IF OOTV IME JJEDNAKO BROJ OZATV naredba
 
class P(Parser):
    def start(p) -> 'Program':
        p.broj_petlji = 0
        p.deklarirane_varijable = set()
        naredbe = [p.naredba()]
        while not p > KRAJ: naredbe.append(p.naredba())
        return Program(naredbe)
    
    def deklaracija(p) -> 'Deklaracija':
        p >> T.INT
        ime = p >> T.IME
        ime_str = ime.sadržaj
        if ime_str in p.deklarirane_varijable:
            raise SemantičkaGreška(f'varijabla {ime_str} je već deklarirana')
        p.deklarirane_varijable.add(ime_str)
        p >> T.TOČKAZ
        return Deklaracija(ime)

    def naredba(p) -> 'Deklaracija|petlja|ispis|grananje|BREAK|CONTINUE|PraznaNaredba|blok':
        if p > T.INT: return p.deklaracija()
        if p > T.FOR: return p.petlja()
        elif p > T.COUT: return p.ispis()
        elif p > T.IF: return p.grananje()
        elif p >= T.TOČKAZ: return PraznaNaredba()
        elif p >= T.VOTV:
            naredbe = []
            while not p >= T.VZATV: naredbe.append(p.naredba())
            return Blok(naredbe)
        elif br := p >= T.BREAK:
            if(p.broj_petlji == 0): raise SemantičkaGreška('nedozvoljen break izvan petlje')
            p >> T.TOČKAZ
            return br
        elif cn := p >> T.CONTINUE:
            p >> T.TOČKAZ
            return cn
     
    def petlja(p) -> 'Petlja':
        kriva_varijabla = SemantičkaGreška(
            'Sva tri dijela for-petlje moraju imati istu varijablu.')
        p >> T.FOR, p >> T.OOTV
        i = p >> T.IME

        if i.sadržaj not in p.deklarirane_varijable:
            raise SemantičkaGreška(f'varijabla {i.sadržaj} nije deklarirana prije upotrebe')

        p >> T.JEDNAKO
        početak = p >> {T.BROJ, T.IME}
        p >> T.TOČKAZ

        if (p >> T.IME) != i: raise kriva_varijabla
        p >> T.MANJE
        granica = p >> {T.BROJ, T.IME}
        p >> T.TOČKAZ

        if (p >> T.IME) != i: raise kriva_varijabla
        if p >= T.PLUSP: inkrement = nenavedeno
        elif p >> T.PLUSJ: inkrement = p >> {T.BROJ, T.IME}
        p >> T.OZATV

        p.broj_petlji += 1
        tijelo = p.naredba()
        p.broj_petlji -= 1
        return Petlja(i, početak, granica, inkrement, tijelo)
        
    def ispis(p) -> 'Ispis':
        p >> T.COUT
        varijable, novired = [], nenavedeno
        while p >= T.MMANJE:
            if varijabla := p >= T.IME: varijable.append(varijabla)
            else:
                novired = p >> T.ENDL
                break
        p >> T.TOČKAZ
        return Ispis(varijable, novired)

    def grananje(p) -> 'Grananje':
        p >> T.IF, p >> T.OOTV
        lijevo = p >> T.IME
        operator = p >> {T.JJEDNAKO, T.MANJE}
        desno = p >> T.BROJ
        p >> T.OZATV
        return Grananje(operator, lijevo, desno, p.naredba())


class Prekid(NelokalnaKontrolaToka): """Signal koji šalje naredba break."""
class Nastavi(NelokalnaKontrolaToka): """Signal koji šalje naredba continue."""


## Apstraktna sintaksna stabla:
# Program: naredbe:[naredba]
# naredba: BREAK: Token
#          CONTINUE: Token
#          Deklaracija: IME
#          PraznaNaredba:
#          Blok: naredbe:[naredba]
#          Petlja: varijabla:IME početak:'T.BROJ|T.IME' granica:'T.BROJ|T.IME'
#                      inkrement:'T.BROJ|T.IME'? tijelo:naredba
#          Ispis: varijable:[IME] novired:ENDL?
#          Grananje: operator:'T.JJEDNAKO|T.MANJE' lijevo:IME desno:BROJ onda:naredba

class Program(AST):
    naredbe: list[P.naredba]

    def izvrši(program):
        rt.mem = Memorija()
        for naredba in program.naredbe: naredba.izvrši()

class Petlja(AST):
    varijabla: T.IME
    početak: 'T.BROJ|T.IME'
    granica: 'T.BROJ|T.IME'
    inkrement: Optional['T.BROJ|T.IME']
    tijelo: P.naredba

    def izvrši(petlja):
        kv = petlja.varijabla  # kontrolna varijabla petlje
        rt.mem[kv] = petlja.početak.vrijednost()
        while rt.mem[kv] < petlja.granica.vrijednost():
            try:
                petlja.tijelo.izvrši()
            except Prekid: break
            except Nastavi: pass
            inkr = petlja.inkrement
            rt.mem[kv] += inkr.vrijednost() if inkr else 1

class Ispis(AST):
    varijable: list[T.IME]
    novired: Optional[T.ENDL]

    def izvrši(ispis):
        for varijabla in ispis.varijable:
            print(varijabla.vrijednost(), end=' ')
        if ispis.novired ^ T.ENDL: print()

class Grananje(AST):
    operator: 'T.JJEDNAKO|T.MANJE'
    lijevo: T.IME
    desno: T.BROJ
    onda: P.naredba

    def izvrši(grananje):
        if grananje.operator ^ T.JJEDNAKO:
            if grananje.lijevo.vrijednost() == grananje.desno.vrijednost():
                grananje.onda.izvrši()
        elif grananje.operator ^ T.MANJE:
            if grananje.lijevo.vrijednost() < grananje.desno.vrijednost():
                grananje.onda.izvrši()

class PraznaNaredba(AST):
    def izvrši(prazna): pass

class Blok(AST):
    naredbe: list[P.naredba]

    def izvrši(blok):
        for naredba in blok.naredbe: naredba.izvrši()

class Deklaracija(AST):
    var: T.IME

    def izvrši(deklaracija):
        rt.mem[deklaracija.var] = 0


def očekuj(greška, kôd):
    print('Testiram:', kôd)
    with greška: P(kôd).izvrši()

prikaz(kôd := P('''
    int i;
    int j;
    for ( i = 8 ; i < 13 ; i += 2 ) {
        for(j=0; j<5; j++) {
            cout<<i<<j;
            if(i == 10) if (j == 1) break;
        }
        cout<<i<<endl;
    }
'''), 8)
kôd.izvrši()
prikaz(P('cout;'))

prikaz(kôd := P('''
    int i;
    for ( i = 0 ; i < 10 ; i++ ) {
        if(i == 4) break;
        cout << i << endl;
    }
'''), 8)
kôd.izvrši()

prikaz(kôd := P('''
    int i;
    for ( i = 0 ; i < 10 ; i++ ) {
        if(i == 4) continue;
        cout << i << endl;
    }
'''), 8)
kôd.izvrši()

prikaz(kôd := P('''int i ; for (i = 0 ; i < 10 ; i++ ) ;'''), 8)
kôd.izvrši()

prikaz(kôd := P('''
    int i;
    for ( i = 0 ; i < 3 ; i++ ) {
        if(i == 1) {
            cout << i;
            cout << i << endl;
        }
    }
'''), 8)
kôd.izvrši()

prikaz(kôd := P('''
    int start;
    int kraj;
    int korak;
    int i;
    for(start = 2; start < 3; start++)
    for(kraj = 10; kraj < 11; kraj++)
    for(korak = 3; korak < 4; korak++)
    for ( i = start ; i < kraj ; i += korak ) {
        cout << i << endl;
    }
'''), 8)
kôd.izvrši()

prikaz(kôd := P('''
    int i;
    for ( i = 0 ; i < 5 ; i++ ) {
        if (i < 3) {
            cout << i << endl;
        }
    }
'''), 8)
kôd.izvrši()

očekuj(SintaksnaGreška, '')
# očekuj(SintaksnaGreška, 'for(c=1; c<3; c++);')
očekuj(LeksičkaGreška, '+1')
očekuj(SemantičkaGreška, 'for(a=1; b<3; c++)break;')
očekuj(SemantičkaGreška, 'break;')
očekuj(LeksičkaGreška, 'if(i == 07) cout;')


# DZ: implementirajte naredbu continue. Rijeseno!
# DZ: implementirajte praznu naredbu (for/if(...);). Rijeseno!
# DZ: omogućite i grananjima da imaju blokove -- uvedite novo AST Blok. Rijeseno!
# DZ: omogućite da parametri petlje budu varijable, ne samo brojevi. Rijeseno!
# DZ: omogućite grananja s obzirom na relaciju <, ne samo ==. Rijeseno!
# DZ: dodajte parseru kontekstnu varijablu 'jesmo li u petlji' za dozvolu BREAK. Rijeseno!
# DZ: uvedite deklaracije varijabli i pratite jesu li varijable deklarirane. Rijeseno!