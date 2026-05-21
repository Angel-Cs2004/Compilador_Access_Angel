.\" Documentacion Tecnica - Compilador Accesible
.\" Universidad Nacional de San Agustin
.\" Groff ms macros
.\"
.nr PS 11
.nr VS 13
.nr HM 1.25i
.nr FM 1.25i
.nr PO 1.25i
.nr LL 6i
.\"
.de CW
.ft CW
..
.de CF
.ft R
..
.\"
.TL
\f[B]COMPILADOR ACCESIBLE\f[R]
.br
\f[I]Documentacion Tecnica\f[R]
.AU
Angel Quispe Suarez
.AI
Universidad Nacional de San Agustin de Arequipa
.br
Escuela Profesional de Ciencias de la Computacion
.br
Curso: Compiladores \(em 2026
.AB no
.AE
.bp
.\"
.\" ============================================================
.\" INDICE
.\" ============================================================
.NH 1
Indice
.PP
.IP "1." 4
Introduccion \&.....................................................\& 3
.IP "2." 4
Arquitectura del Sistema \&.........................................\& 4
.IP "3." 4
El Lenguaje Accesible (.acc) \&....................................\& 5
.IP "4." 4
Gramatica Formal (EBNF) \&..........................................\& 7
.IP "5." 4
Analizador Lexico (Fase 1) \&......................................\& 9
.IP "6." 4
Analizador Sintactico (Fase 2) \&..................................\& 12
.IP "7." 4
Arbol de Sintaxis Abstracta (AST) \&...............................\& 14
.IP "8." 4
Deteccion y Reporte de Errores \&..................................\& 16
.IP "9." 4
Uso del Compilador \&...............................................\& 17
.IP "10." 4
Ejemplos Completos \&...............................................\& 18
.IP "11." 4
Conclusiones \&.....................................................\& 20
.bp
.\"
.\" ============================================================
.\" 1. INTRODUCCION
.\" ============================================================
.NH 1
Introduccion
.PP
La ensenanza de la programacion enfrenta barreras significativas que van mas alla
del dominio conceptual de los algoritmos.
Los lenguajes de programacion tradicionales como C, Java o Python emplean una
sintaxis cargada de simbolos crípticos: llaves
.CW
{}
.CF
para delimitar bloques, barras verticales
.CW
||
.CF
para la disyuncion logica, puntos y comas
.CW
;
.CF
para terminar instrucciones, y operadores como
.CW
&&
.CF
o
.CW
!=
.CF
cuyo significado no resulta intuitivo para hablantes de espanol.
.PP
Esta carga simbolica representa una barrera especialmente severa para estudiantes
con discapacidades sensoriales.
Para un alumno con baja vision o ceguera que utiliza un lector de pantalla,
distinguir entre
.CW
{
.CF
y
.CW
}
,
.CW
(
.CF
y
.CW
)
, o entre
.CW
=
.CF
y
.CW
==
.CF
es una tarea cognitivamente agotadora que distrae de la comprension del problema
real que se intenta resolver.
Para un alumno sordo cuyo primer idioma es la Lengua de Senas, la gramatica
del espanol escrito ya supone un reto; anadir encima una segunda "lengua"
de simbolos matematicos eleva el umbral de entrada de manera desproporcionada.
.NH 2
Magnitud del Problema
.PP
Estudios recientes sobre aprendizaje de programacion arrojan cifras preocupantes:
.IP \(bu 3
Entre el
.B "50 y 73 por ciento"
del codigo fuente producido por estudiantes en sus primeros semestres
.I "no compila"
debido a errores de sintaxis.
.IP \(bu 3
Solo el
.B "2 por ciento"
de los profesionales tecnologicos reporta algun tipo de discapacidad,
frente al
.B "19 por ciento"
de la poblacion general,
lo que evidencia una exclusion sistematica desde la etapa educativa.
.IP \(bu 3
Los mensajes de error de compiladores clasicos suelen ser tecnicos y en ingles,
lo que agrava la situacion para estudiantes hispanohablantes con discapacidad.
.NH 2
La Solucion Propuesta
.PP
El
.B "Compilador Accesible"
es un proyecto academico desarrollado en el marco del curso de Compiladores de la
Universidad Nacional de San Agustin.
Su objetivo central es construir un compilador completo para un lenguaje de
programacion basado en espanol natural, eliminando los simbolos crípticos y
reemplazandolos por palabras clave familiares.
.PP
El lenguaje resultante,
de extension
.B .acc
(por
.I "accesible"
),
permite escribir programas como:
.DS I
.CW
definir area como base por altura
si area es mayor que 100 entonces
    mostrar "Area grande"
sino
    mostrar "Area normal"
fin si
.CF
.DE
.PP
Este codigo es legible por cualquier hispanohablante sin conocimientos previos
de programacion formal.
La propuesta no es un reemplazante de los lenguajes profesionales,
sino una
.I "puerta de entrada"
que reduce la carga cognitiva en la fase inicial del aprendizaje.
.bp
.\"
.\" ============================================================
.\" 2. ARQUITECTURA DEL SISTEMA
.\" ============================================================
.NH 1
Arquitectura del Sistema
.PP
El compilador implementa un
.B "pipeline de dos fases"
que transforma un archivo de texto fuente
.B .acc
en un Arbol de Sintaxis Abstracta (AST) completamente validado.
La arquitectura sigue el diseno clasico de un compilador de vanguardia frontal
.I "(front-end)"
desacoplado de cualquier generacion de codigo, lo que permite extenderlo hacia
fases de analisis semantico y generacion en futuras iteraciones.
.NH 2
Pipeline de Procesamiento
.PP
El flujo de datos sigue la secuencia:
.DS I
.CW
Archivo .acc
     |
     v
+------------------+
|  Analizador      |   Fase 1: Analisis Lexico
|  Lexico (Lexer)  |   Lee caracter a caracter
|                  |   Produce lista de tokens
+------------------+
     |
     v  Lista de tokens
+------------------+
|  Analizador      |   Fase 2: Analisis Sintactico
|  Sintactico      |   Verifica la gramatica
|  (Parser)        |   Construye el AST
+------------------+
     |
     v
   AST validado
.CF
.DE
.NH 2
Estructura de Archivos
.PP
El proyecto sigue una organizacion modular clara:
.TS
allbox center;
lB lB
l l.
Archivo	Responsabilidad
src/token.hpp, token.cpp	Definicion de tipos de token y estructura Token
src/lexer.hpp, lexer.cpp	Analizador lexico: texto -> lista de tokens
src/ast.hpp, ast.cpp	Nodos del Arbol de Sintaxis Abstracta
src/parser.hpp, parser.cpp	Analizador sintactico: tokens -> AST
src/main.cpp	Punto de entrada, manejo de argumentos CLI
ejemplos/	Programas de ejemplo .acc (basico, completo, etc.)
Makefile	Reglas de compilacion con g++
.TE
.NH 2
Tecnologia Utilizada
.PP
El nucleo del compilador esta implementado en
.B "C++ estandar (C++17)"
sin dependencias externas, lo que facilita la compilacion en cualquier plataforma
con
.CW
g++
.CF
o
.CW
clang++
.CF
disponibles.
Se hace uso extensivo de la biblioteca estandar:
.CW
std::string
.CF
,
.CW
std::vector
.CF
,
.CW
std::unordered_map
.CF
y herencia polimórfica para los nodos del AST.
.bp
.\"
.\" ============================================================
.\" 3. EL LENGUAJE ACCESIBLE (.acc)
.\" ============================================================
.NH 1
El Lenguaje Accesible (.acc)
.NH 2
Principios de Diseno
.PP
El lenguaje
.B .acc
fue disenado respetando los siguientes principios:
.IP "1." 4
.B "Palabras clave en espanol natural:"
Toda la sintaxis emplea vocabulario castellano cotidiano.
No existe ningun simbolo de puntuacion obligatorio.
.IP "2." 4
.B "Insensible a mayusculas:"
El lexer normaliza todo a minusculas antes de clasificar,
por lo que
.CW
Definir
.CF
,
.CW
DEFINIR
.CF
y
.CW
definir
.CF
son equivalentes.
.IP "3." 4
.B "Estructura por sangria semantica y palabras de cierre:"
Los bloques se delimitan con palabras de cierre explícitas
.CW
(fin si, fin repetir, fin mientras)
.CF
en lugar de llaves, lo que es mas amigable con lectores de pantalla.
.IP "4." 4
.B "Un concepto, una linea:"
Cada instruccion ocupa una linea, simplificando el analisis y los mensajes
de error.
.IP "5." 4
.B "Operadores aritmeticos como palabras:"
.CW
mas, menos, por, entre
.CF
reemplazan a
.CW
+, -, *, /
.CF
respectivamente.
.NH 2
Construcciones del Lenguaje
.PP
A continuacion se presentan todas las construcciones soportadas con ejemplos:
.PP
.B "Declaracion de Variables"
.DS I
.CW
definir nombre como 5
definir mensaje como "Hola mundo"
definir activo como verdadero
.CF
.DE
.PP
La palabra clave
.CW
definir
.CF
introduce una nueva variable;
.CW
como
.CF
asigna el valor de la expresion a la derecha.
El tipo es inferido del literal.
.PP
.B "Condicional (si / sino / fin si)"
.DS I
.CW
si edad es mayor o igual que 18 entonces
    mostrar "Mayor de edad"
sino
    mostrar "Menor de edad"
fin si
.CF
.DE
.PP
La rama
.CW
sino
.CF
es opcional.
El bloque de instrucciones termina con
.CW
fin si
.CF
.
.PP
.B "Bucle Repetir (repetir N veces)"
.DS I
.CW
repetir 5 veces
    mostrar "iteracion"
fin repetir
.CF
.DE
.PP
Repite el bloque el numero de veces especificado.
La expresion de conteo puede ser cualquier expresion aritmetica.
.PP
.B "Bucle Mientras (mientras / fin mientras)"
.DS I
.CW
definir i como 0
mientras i es menor que 10
    definir i como i mas 1
fin mientras
.CF
.DE
.PP
Ejecuta el bloque mientras la condicion sea verdadera.
.PP
.B "Salida de Datos (mostrar)"
.DS I
.CW
mostrar "El resultado es: "
mostrar area
mostrar base por altura
.CF
.DE
.PP
.B "Comentarios"
.DS I
.CW
# Esto es un comentario, se ignora por el compilador
definir x como 10  # comentario al final de una linea
.CF
.DE
.NH 2
Operadores
.PP
.B "Operadores de Comparacion:"
.TS
allbox center;
lB lB
l l.
Operador en .acc	Equivalente matematico
es igual a	=
es mayor que	>
es menor que	<
es mayor o igual que	>=
es menor o igual que	<=
.TE
.PP
.B "Operadores Aritmeticos:"
.TS
allbox center;
lB lB
l l.
Operador en .acc	Equivalente
mas	+
menos	-
por	*
entre	/
.TE
.PP
.B "Operadores Logicos:"
.TS
allbox center;
lB lB
l l.
Operador en .acc	Significado
y	Conjuncion logica (AND)
o	Disyuncion logica (OR)
no	Negacion logica (NOT)
.TE
.bp
.\"
.\" ============================================================
.\" 4. GRAMATICA FORMAL (EBNF)
.\" ============================================================
.NH 1
Gramatica Formal (EBNF)
.PP
La gramatica completa del lenguaje
.B .acc
se define a continuacion en notacion EBNF.
Los simbolos entre comillas dobles son terminales (tokens).
El asterisco
.CW
*
.CF
indica cero o mas repeticiones;
el signo de interrogacion
.CW
?
.CF
indica elemento opcional.
.NH 2
Reglas de Produccion
.DS I
.CW
programa         -> instruccion*

instruccion      -> declaracion
                  | condicional
                  | bucle_repetir
                  | bucle_mientras
                  | salida

declaracion      -> "definir" IDENTIFICADOR "como" expresion NEWLINE

condicional      -> "si" condicion "entonces" NEWLINE
                       instruccion*
                   ("sino" NEWLINE
                       instruccion*)?
                   "fin" "si"

bucle_repetir    -> "repetir" expresion "veces" NEWLINE
                       instruccion*
                   "fin" "repetir"

bucle_mientras   -> "mientras" condicion NEWLINE
                       instruccion*
                   "fin" "mientras"

salida           -> "mostrar" expresion NEWLINE

expresion        -> termino (("mas" | "menos") termino)*

termino          -> factor (("por" | "entre") factor)*

factor           -> NUMERO
                  | TEXTO
                  | IDENTIFICADOR
                  | "(" expresion ")"

condicion        -> ["no"] condicion_base
                       (("y" | "o") condicion_base)*

condicion_base   -> expresion comparador expresion

comparador       -> "es" "igual" "a"
                  | "es" "mayor" "que"
                  | "es" "menor" "que"
                  | "es" "mayor" "o" "igual" "que"
                  | "es" "menor" "o" "igual" "que"
.CF
.DE
.NH 2
Terminales
.PP
Los tokens terminales se definen con las siguientes expresiones regulares:
.TS
allbox center;
lB lB
l l.
Terminal	Patron
NUMERO	[0-9]+ ( "." [0-9]+ )?
TEXTO	["] ( caracter | \\n | \\t )* ["]
IDENTIFICADOR	[a-zA-Z_][a-zA-Z0-9_]*
VERDADERO	"verdadero"
FALSO	"falso"
NUEVA_LINEA	\\n (salto de linea)
COMENTARIO	# .* \\n  (descartado)
.TE
.PP
Todos los identificadores y palabras clave son tratados con
.I "case-insensitive matching"
: el lexer convierte cada token a minusculas antes de clasificarlo,
de modo que
.CW
MOSTRAR
.CF
y
.CW
Mostrar
.CF
son equivalentes a
.CW
mostrar
.CF
.
.NH 2
Ambiguedad y Precedencia
.PP
La gramatica resuelve la ambiguedad de operadores aritmeticos mediante la
jerarquia clasica de la teoria de compiladores:
.IP \(bu 3
.B "Menor precedencia:"
.CW
mas
.CF
y
.CW
menos
.CF
(aditivos) se manejan en la regla
.CW
expresion
.CF
.
.IP \(bu 3
.B "Mayor precedencia:"
.CW
por
.CF
y
.CW
entre
.CF
(multiplicativos) se manejan en la regla
.CW
termino
.CF
, que es llamada por
.CW
expresion
.CF
.
.IP \(bu 3
.B "Maximo nivel:"
Los atomos (numeros, textos, identificadores y expresiones entre parentesis)
se manejan en
.CW
factor
.CF
.
.PP
Esta estratificacion garantiza que
.CW
2 mas 3 por 4
.CF
se interprete como
.CW
2 + (3 * 4) = 14
.CF
y no como
.CW
(2 + 3) * 4 = 20
.CF
.
.bp
.\"
.\" ============================================================
.\" 5. ANALIZADOR LEXICO (Fase 1)
.\" ============================================================
.NH 1
Analizador Lexico (Fase 1)
.NH 2
Funcion y Responsabilidades
.PP
El analizador lexico, implementado en
.CW
src/lexer.hpp
.CF
y
.CW
src/lexer.cpp
.CF
,
es el primer componente del pipeline de compilacion.
Su tarea es leer el archivo fuente
.B caracter por caracter
y agrupar secuencias de caracteres en unidades significativas denominadas
.B tokens
.
.PP
Concretamente, el lexer se encarga de:
.IP \(bu 3
Eliminar espacios en blanco y tabulaciones irrelevantes.
.IP \(bu 3
Reconocer y descartar comentarios (lineas que comienzan con
.CW
#
.CF
o comentarios al final de linea).
.IP \(bu 3
Identificar palabras clave del lenguaje.
.IP \(bu 3
Reconocer identificadores de variables.
.IP \(bu 3
Reconocer literales numericos (enteros y decimales).
.IP \(bu 3
Reconocer literales de texto entre comillas dobles, con soporte para secuencias
de escape (
.CW
\\n
.CF
,
.CW
\\t
.CF
).
.IP \(bu 3
Emitir tokens de nueva linea (
.CW
NUEVA_LINEA
.CF
) que el parser necesita para delimitar instrucciones.
.IP \(bu 3
Registrar y reportar errores lexicos con numero de linea y columna exactos.
.NH 2
Estructura del Token
.PP
Cada token producido por el lexer es una instancia de la estructura
.CW
Token
.CF
definida en
.CW
src/token.hpp
.CF
:
.DS I
.CW
struct Token {
    TipoToken tipo;    // Categoria del token (enum)
    string    valor;   // Lexema exacto del codigo fuente
    int       linea;   // Linea donde aparece (base 1)
    int       columna; // Columna donde comienza (base 1)
};
.CF
.DE
.NH 2
Categorias de Tokens
.PP
El enum
.CW
TipoToken
.CF
clasifica todos los tokens posibles:
.TS
allbox center;
lB lB
l l.
Categoria	Tokens
Palabras clave	DEFINIR, COMO, SI, ENTONCES, SINO, FIN
Palabras clave (cont.)	REPETIR, VECES, MIENTRAS, MOSTRAR
Comparacion	ES, MAYOR, MENOR, IGUAL, QUE, A, O
Aritmetica	MAS, MENOS, POR, ENTRE
Logicos	Y, O_OP, NO
Literales	NUMERO, TEXTO, VERDADERO, FALSO
Identificadores	IDENTIFICADOR
Puntuacion	PAREN_IZQ, PAREN_DER
Control	NUEVA_LINEA, FIN_ARCHIVO
Errores	ERROR
.TE
.NH 2
La Clase Lexer
.PP
La clase principal
.CW
Lexer
.CF
expone la interfaz:
.DS I
.CW
class Lexer {
public:
    Lexer(const string& codigo_fuente);
    vector<Token> tokenizar();   // Metodo principal

private:
    string fuente;
    int pos, linea, columna;
    unordered_map<string, TipoToken> PALABRAS_CLAVE;

    char actual();
    char siguiente();
    void avanzar();
    Token leerNumero();
    Token leerTexto();
    Token leerPalabraOIdentificador();
    void saltarComentario();
};
.CF
.DE
.PP
El metodo central es
.CW
tokenizar()
.CF
,
que itera sobre el texto fuente en un bucle principal y, dependiendo del
caracter actual, delega a uno de los metodos especializados de lectura.
.NH 2
Algoritmo de Tokenizacion
.PP
El algoritmo principal sigue el patron de
.I "automata de estados finito":
.IP "1." 4
Leer el caracter actual.
.IP "2." 4
Si es un espacio o tabulacion: avanzar y continuar.
.IP "3." 4
Si es un salto de linea (
.CW
\\n
.CF
): emitir token
.CW
NUEVA_LINEA
.CF
, incrementar contador de linea.
.IP "4." 4
Si es
.CW
#
.CF
: llamar a
.CW
saltarComentario()
.CF
y continuar.
.IP "5." 4
Si es un digito: llamar a
.CW
leerNumero()
.CF
.
.IP "6." 4
Si es
.CW
"
.CF
: llamar a
.CW
leerTexto()
.CF
.
.IP "7." 4
Si es
.CW
(
.CF
o
.CW
)
.CF
: emitir token de parentesis correspondiente.
.IP "8." 4
Si es letra o guion bajo: llamar a
.CW
leerPalabraOIdentificador()
.CF
.
.IP "9." 4
De lo contrario: emitir token de tipo
.CW
ERROR
.CF
con el caracter desconocido.
.NH 2
Reconocimiento de Palabras Clave
.PP
El metodo
.CW
leerPalabraOIdentificador()
.CF
lee todos los caracteres alfanumericos consecutivos,
los convierte a minusculas y busca el resultado en el mapa hash
.CW
PALABRAS_CLAVE
.CF
.
Si hay coincidencia, se emite el tipo de palabra clave correspondiente.
En caso contrario, se emite un token
.CW
IDENTIFICADOR
.CF
.
Esta estrategia centraliza el reconocimiento de palabras reservadas y
facilita agregar nuevas palabras clave en un solo lugar del codigo.
.NH 2
Ejemplo de Tokenizacion
.PP
Dado el siguiente fragmento de codigo fuente:
.DS I
.CW
definir contador como 1
.CF
.DE
.PP
El lexer produce la siguiente secuencia de tokens:
.TS
allbox center;
lB lB lB lB
l l l l.
Tipo	Valor	Linea	Columna
DEFINIR	definir	1	1
IDENTIFICADOR	contador	1	9
COMO	como	1	18
NUMERO	1	1	23
NUEVA_LINEA	\\n	1	24
.TE
.NH 2
Tratamiento de Literales Especiales
.PP
.B "Numeros Decimales:"
El metodo
.CW
leerNumero()
.CF
detecta la presencia de un punto decimal y continua leyendo
digitos tras el, produciendo un unico token
.CW
NUMERO
.CF
con valor
.CW
"3.14"
.CF
.
.PP
.B "Cadenas con Secuencias de Escape:"
.CW
leerTexto()
.CF
procesa el contenido entre comillas y sustituye la secuencia
.CW
\\n
.CF
por salto de linea real y
.CW
\\t
.CF
por tabulacion.
Si la cadena no se cierra antes del fin del archivo, el lexer emite un
token
.CW
ERROR
.CF
con el mensaje
.I "cadena de texto no cerrada"
.
.bp
.\"
.\" ============================================================
.\" 6. ANALIZADOR SINTACTICO (Fase 2)
.\" ============================================================
.NH 1
Analizador Sintactico (Fase 2)
.NH 2
Funcion y Responsabilidades
.PP
El analizador sintactico (
.I parser
), implementado en
.CW
src/parser.hpp
.CF
y
.CW
src/parser.cpp
.CF
,
recibe la lista de tokens producida por el lexer y verifica que su estructura
se ajuste a la gramatica formal del lenguaje
.B .acc
.
Si la estructura es valida, construye un
.B "Arbol de Sintaxis Abstracta (AST)"
que representa fielmente la jerarquia logica del programa.
.PP
Las responsabilidades concretas del parser incluyen:
.IP \(bu 3
Confirmar que cada instruccion comienza con una palabra clave valida.
.IP \(bu 3
Verificar que los bloques condicionales y de bucle cuenten con sus palabras
de cierre (
.CW
fin si
.CF
,
.CW
fin repetir
.CF
,
.CW
fin mientras
.CF
).
.IP \(bu 3
Verificar la presencia de palabras clave intermedias obligatorias (
.CW
entonces
.CF
,
.CW
veces
.CF
,
.CW
como
.CF
).
.IP \(bu 3
Construir nodos del AST para cada construccion reconocida.
.IP \(bu 3
Reportar errores sintacticos con ubicacion exacta (linea y columna).
.NH 2
Estrategia de Analisis: Descenso Recursivo
.PP
El parser implementa la tecnica de
.B "descenso recursivo predictivo"
.I "(recursive descent parser)"
: cada regla de la gramatica se implementa como un metodo C++ independiente.
El parser mantiene un puntero al token actual y avanza mediante el metodo
.CW
consumir()
.CF
,
que verifica que el token actual sea del tipo esperado y avanza al siguiente.
Si el tipo no coincide, se lanza una excepcion con el mensaje de error apropiado.
.NH 2
Correspondencia Gramatica-Metodos
.PP
La siguiente tabla muestra la correspondencia entre reglas gramaticales y
metodos del parser:
.TS
allbox center;
lB lB
l l.
Metodo C++	Regla Gramatical
parsear()	programa
parsearInstruccion()	instruccion (despachador)
parsearDeclaracion()	declaracion
parsearCondicional()	condicional
parsearBucleRepetir()	bucle_repetir
parsearBucleMientras()	bucle_mientras
parsearMostrar()	salida
parsearExpresion()	expresion
parsearTermino()	termino
parsearFactor()	factor
parsearCondicion()	condicion
parsearComparador()	comparador
.TE
.NH 2
Flujo del Metodo Principal
.PP
El metodo
.CW
parsear()
.CF
implementa la regla
.CW
programa -> instruccion*
.CF
:
.DS I
.CW
NodoPrograma* parsear() {
    auto programa = new NodoPrograma();
    saltarNuevasLineas();
    while (!esFin()) {
        programa->instrucciones.push_back(
            parsearInstruccion()
        );
        saltarNuevasLineas();
    }
    return programa;
}
.CF
.DE
.PP
El metodo
.CW
parsearInstruccion()
.CF
actua como un
.I despachador
que examina el tipo del token actual y llama al metodo especifico:
.DS I
.CW
NodoBase* parsearInstruccion() {
    switch (tokenActual().tipo) {
        case DEFINIR:  return parsearDeclaracion();
        case SI:       return parsearCondicional();
        case REPETIR:  return parsearBucleRepetir();
        case MIENTRAS: return parsearBucleMientras();
        case MOSTRAR:  return parsearMostrar();
        default:
            error("Instruccion desconocida");
    }
}
.CF
.DE
.NH 2
Manejo de Bloques Anidados
.PP
Los bloques pueden anidarse a cualquier profundidad.
El parser maneja el anidamiento naturalmente gracias al descenso recursivo:
cuando
.CW
parsearCondicional()
.CF
llama a
.CW
parsearInstruccion()
.CF
en su cuerpo,
y esa instruccion resulta ser otro
.CW
si
.CF
,
se realiza una nueva llamada recursiva a
.CW
parsearCondicional()
.CF
.
El retorno de la recursion despila el contexto correctamente.
.bp
.\"
.\" ============================================================
.\" 7. AST
.\" ============================================================
.NH 1
Arbol de Sintaxis Abstracta (AST)
.NH 2
Que es el AST
.PP
El
.B "Arbol de Sintaxis Abstracta"
es una representacion jerarquica en memoria de la estructura logica de un programa.
A diferencia del arbol de parseo concreto, el AST omite los detalles
de la gramatica que no tienen relevancia semantica (como los tokens de
nueva linea o las palabras de cierre), conservando unicamente la informacion
estructural necesaria para las fases posteriores del compilador.
.NH 2
Jerarquia de Nodos
.PP
Todos los nodos del AST heredan de la clase base abstracta
.CW
Nodo
.CF
,
que declara el metodo virtual puro
.CW
imprimir()
.CF
y el destructor virtual:
.DS I
.CW
class Nodo {
public:
    virtual ~Nodo() = default;
    virtual void imprimir(int nivel = 0) const = 0;
};
.CF
.DE
.PP
La jerarquia completa de nodos es:
.DS I
.CW
Nodo (clase base abstracta)
|
+-- NodoNumero          (literal numerico)
+-- NodoTexto           (literal de cadena)
+-- NodoBooleano        (verdadero / falso)
+-- NodoIdentificador   (nombre de variable)
+-- NodoOpBinaria       (operacion aritmetica: izq, op, der)
+-- NodoComparacion     (comparacion: izq, comparador, der)
+-- NodoOpLogica        (logica binaria: izq, y/o, der)
+-- NodoNegar           (negacion logica: operando)
+-- NodoDeclaracion     (nombre de variable, expresion)
+-- NodoCondicional     (condicion, bloque_si, bloque_sino)
+-- NodoBucleRepetir    (expresion_veces, cuerpo)
+-- NodoBucleMientras   (condicion, cuerpo)
+-- NodoMostrar         (expresion)
+-- NodoPrograma        (vector de instrucciones)
.CF
.DE
.NH 2
Ejemplo de AST Generado
.PP
Para el siguiente codigo fuente:
.DS I
.CW
definir area como base por altura
.CF
.DE
.PP
El parser construye el siguiente arbol:
.DS I
.CW
NodoPrograma
  |
  +-- NodoDeclaracion [nombre="area"]
        |
        +-- NodoOpBinaria [operador="por"]
              |
              +-- izquierda: NodoIdentificador [nombre="base"]
              |
              +-- derecha:   NodoIdentificador [nombre="altura"]
.CF
.DE
.PP
Para un programa mas completo con condicional:
.DS I
.CW
si area es mayor que 40 entonces
    mostrar "Area grande"
fin si
.CF
.DE
.PP
El AST correspondiente es:
.DS I
.CW
NodoPrograma
  |
  +-- NodoCondicional
        |
        +-- condicion: NodoComparacion [op="es mayor que"]
        |     |
        |     +-- izq: NodoIdentificador [nombre="area"]
        |     +-- der: NodoNumero [valor="40"]
        |
        +-- bloque_entonces:
        |     +-- NodoMostrar
        |           +-- NodoTexto [valor="Area grande"]
        |
        +-- bloque_sino: (vacio)
.CF
.DE
.NH 2
Visualizacion del AST
.PP
El metodo
.CW
imprimir()
.CF
de cada nodo produce una representacion textual con sangria proporcional
al nivel de profundidad del nodo.
Esto permite al usuario del compilador invocar
.CW
./compilador --ast archivo.acc
.CF
y obtener una vista legible del arbol completo, util para depuracion y
verificacion pedagogica.
.bp
.\"
.\" ============================================================
.\" 8. DETECCION Y REPORTE DE ERRORES
.\" ============================================================
.NH 1
Deteccion y Reporte de Errores
.NH 2
Errores Lexicos
.PP
El analizador lexico detecta los siguientes tipos de error:
.TS
allbox center;
lB lB lB
l l l.
Error	Causa	Ejemplo
Caracter desconocido	Simbolo no perteneciente al lenguaje	@ # $ %
Cadena no cerrada	Falta comilla de cierre antes del EOF	"hola mundo
.TE
.NH 2
Errores Sintacticos
.PP
El analizador sintactico detecta errores de estructura:
.TS
allbox center;
lB lB
l l.
Error	Descripcion
Falta 'entonces'	Condicional sin la palabra clave 'entonces'
Falta 'como'	Declaracion sin la palabra clave 'como'
Falta 'veces'	Bucle repetir sin la palabra clave 'veces'
Instruccion desconocida	Token inicial no es palabra clave valida
Falta 'fin si'	Bloque condicional sin cierre
Falta 'fin repetir'	Bucle repetir sin cierre
Falta 'fin mientras'	Bucle mientras sin cierre
.TE
.NH 2
Formato de los Mensajes de Error
.PP
Todos los errores siguen el formato unificado:
.DS I
.CW
[Linea X, Col Y] <descripcion del error>
  <linea del codigo fuente>
  <^--- indicador de posicion>
.CF
.DE
.PP
Ejemplo de error lexico:
.DS I
.CW
[Linea 3, Col 15] caracter desconocido: '@'
  definir x como @valor
                ^
.CF
.DE
.PP
Ejemplo de error sintactico:
.DS I
.CW
[Linea 7, Col 1] se esperaba 'entonces' despues de la condicion
  si edad es mayor que 18
  ^
.CF
.DE
.PP
Este formato, inspirado en los mensajes de compiladores modernos como
.CW
clang
.CF
,
proporciona al estudiante toda la informacion necesaria para localizar y
corregir el error: numero de linea, numero de columna, descripcion en espanol
y visualizacion del contexto.
.NH 2
Recuperacion de Errores
.PP
En la version actual del compilador, la deteccion de un error detiene el
procesamiento y reporta el primer error encontrado.
Esta estrategia
.I "(fail-fast)"
es apropiada para un entorno de aprendizaje donde se desea que el estudiante
corrija un error a la vez, evitando la cascada de mensajes de error que
puede resultar confusa.
.bp
.\"
.\" ============================================================
.\" 9. USO DEL COMPILADOR
.\" ============================================================
.NH 1
Uso del Compilador
.NH 2
Compilacion del Proyecto
.PP
El proyecto incluye un
.CW
Makefile
.CF
que automatiza la compilacion con
.CW
g++
.CF
:
.DS I
.CW
make
.CF
.DE
.PP
Esto compila todos los archivos fuente de
.CW
src/
.CF
y produce el ejecutable
.CW
compilador
.CF
en el directorio raiz del proyecto.
.NH 2
Modos de Ejecucion
.PP
El compilador soporta los siguientes modos de operacion:
.TS
allbox center;
lB lB
l l.
Comando	Descripcion
./compilador archivo.acc	Ejecuta ambas fases: lexer y construccion de AST
./compilador --tokens archivo.acc	Solo fase 1: muestra la tabla de tokens
./compilador --ast archivo.acc	Solo fase 2: muestra el arbol AST en texto
./compilador --check archivo.acc	Validacion silenciosa con reporte de errores
./compilador --help	Muestra la ayuda y lista de opciones
./compilador	Modo interactivo: lee instrucciones desde stdin
.TE
.NH 2
Ejemplo de Salida en Modo Tokens
.PP
Para
.CW
./compilador --tokens ejemplos/basico.acc
.CF
:
.DS I
.CW
=== TOKENS ===
[1:1 ] DEFINIR        "definir"
[1:9 ] IDENTIFICADOR  "contador"
[1:18] COMO           "como"
[1:23] NUMERO         "1"
[1:24] NUEVA_LINEA    "\n"
...
[EOF ] FIN_ARCHIVO    ""
.CF
.DE
.NH 2
Ejemplo de Salida en Modo AST
.PP
Para
.CW
./compilador --ast ejemplos/completo.acc
.CF
:
.DS I
.CW
=== ARBOL DE SINTAXIS ABSTRACTA ===
Programa
  Declaracion [base]
    Numero: 5
  Declaracion [altura]
    Numero: 10
  Declaracion [area]
    OpBinaria [por]
      Identificador: base
      Identificador: altura
  Mostrar
    Texto: "Calculando area del rectangulo"
  Mostrar
    Identificador: area
  Condicional
    Comparacion [es mayor que]
      Identificador: area
      Numero: 40
    Bloque-entonces:
      Mostrar
        Texto: "Area grande"
    Bloque-sino:
      Mostrar
        Texto: "Area pequena"
  ...
.CF
.DE
.bp
.\"
.\" ============================================================
.\" 10. EJEMPLOS COMPLETOS
.\" ============================================================
.NH 1
Ejemplos Completos
.NH 2
Programa completo.acc
.PP
El archivo
.CW
ejemplos/completo.acc
.CF
es el programa de referencia que ejercita todas las construcciones del
lenguaje.
Se presenta a continuacion con anotaciones:
.DS I
.CW
# Ejemplo completo: usa todas las estructuras del lenguaje

# 1. Declaraciones de variables y operacion aritmetica
definir base como 5
definir altura como 10
definir area como base por altura

# 2. Salida de texto y valores numericos
mostrar "Calculando area del rectangulo"
mostrar area

# 3. Condicional con comparacion numerica
si area es mayor que 40 entonces
    mostrar "Area grande"
sino
    mostrar "Area pequena"
fin si

# 4. Bucle repetir con acumulador
definir suma como 0
repetir 5 veces
    definir suma como suma mas base
fin repetir
mostrar suma

# 5. Bucle mientras con condicion de parada
definir i como 10
mientras i es mayor que 0
    definir i como i menos 3
fin mientras
mostrar i

# 6. Condicion con operadores logicos compuestos
definir x como 7
si x es mayor que 5 y x es menor que 10 entonces
    mostrar "x esta entre 5 y 10"
fin si
.CF
.DE
.NH 2
Explicacion del Programa
.PP
El programa ilustra las seis construcciones principales del lenguaje:
.IP "Parte 1." 4
.B "Declaraciones."
Se crean tres variables:
.CW
base
.CF
con valor 5,
.CW
altura
.CF
con valor 10 y
.CW
area
.CF
calculada como el producto de las dos anteriores.
Muestra que una expresion aritmetica puede aparecer directamente como valor
de una declaracion.
.IP "Parte 2." 4
.B "Salida mixta."
Se usa
.CW
mostrar
.CF
dos veces: una con un literal de texto y otra con una variable.
.IP "Parte 3." 4
.B "Condicional completo."
Se evalua si
.CW
area
.CF
(que vale 50) es mayor que 40; como la condicion es verdadera,
se muestra "Area grande".
La rama
.CW
sino
.CF
se incluye para demostrar la sintaxis completa.
.IP "Parte 4." 4
.B "Bucle repetir."
Se repite 5 veces la instruccion que acumula
.CW
base
.CF
en
.CW
suma
.CF
.
Al terminar,
.CW
suma
.CF
vale 25 (5 x 5).
.IP "Parte 5." 4
.B "Bucle mientras."
Se decrementa
.CW
i
.CF
de 10 en pasos de 3 hasta que deja de ser mayor que 0.
El valor final de
.CW
i
.CF
sera \(mi2 (10 \(mi 3 \(mi 3 \(mi 3 = 1, luego 1 \(mi 3 = \(mi2).
.IP "Parte 6." 4
.B "Logica compuesta."
Se verifica que
.CW
x
.CF
(igual a 7) cumple simultaneamente dos condiciones:
ser mayor que 5 y menor que 10.
El operador
.CW
y
.CF
combina ambas comparaciones.
.bp
.\"
.\" ============================================================
.\" 11. CONCLUSIONES
.\" ============================================================
.NH 1
Conclusiones
.PP
El
.B "Compilador Accesible"
demuestra que es tecnicamente viable construir un front-end de compilador
completo para un lenguaje basado en espanol natural, con las siguientes
caracteristicas verificadas:
.IP "1." 4
.B "Tokenizacion correcta del espanol natural."
El analizador lexico procesa palabras clave de varias palabras
(como "es mayor o igual que"), literales decimales, cadenas con secuencias
de escape y comentarios de linea, produciendo una secuencia de tokens
limpia y precisa para todas las construcciones definidas.
.IP "2." 4
.B "Validacion estructural completa."
El analizador sintactico de descenso recursivo verifica que la estructura
del programa se ajuste estrictamente a la gramatica formal definida en
EBNF, garantizando la correctitud de cada instruccion antes de proceder.
.IP "3." 4
.B "Construccion de un AST coherente."
El parser produce un Arbol de Sintaxis Abstracta con la jerarquia correcta
de nodos, preservando la informacion necesaria para que fases posteriores
(analisis semantico, generacion de codigo) puedan operar sobre ella.
.IP "4." 4
.B "Mensajes de error contextuales y precisos."
Cada error lexico o sintactico incluye numero de linea, columna, descripcion
en espanol y visualizacion del contexto, permitiendo al estudiante localizar
y corregir el problema de manera autonoma.
.IP "5." 4
.B "Gramatica extensible."
El diseno modular del lexer (tabla hash de palabras clave) y el patron
de descenso recursivo del parser hacen que agregar nuevas palabras clave
o construcciones requiera cambios minimos y localizados.
.IP "6." 4
.B "Base para fases futuras."
La arquitectura actual establece una base solida para implementar:
un
.I "analizador semantico"
que verifique tipos y variables declaradas,
una
.I "tabla de simbolos"
para gestionar alcances,
y un
.I "generador de codigo"
que produzca codigo intermedio o nativo.
.PP
En terminos de impacto educativo, el proyecto confirma la hipotesis inicial:
un lenguaje de programacion basado en palabras del espanol cotidiano
reduce significativamente la carga cognitiva asociada a la sintaxis,
permitiendo que los estudiantes\(emincluidos aquellos con discapacidades
sensoriales\(emse concentren en el aprendizaje de los conceptos algoritmicos
en lugar de batallar con simbolos crípticos.
.PP
El
.B "Compilador Accesible"
no pretende reemplazar a los lenguajes profesionales,
sino abrir una puerta de entrada mas inclusiva al mundo de la programacion,
alineada con los principios del
.I "diseno universal para el aprendizaje (DUA)"
y con el compromiso de la Universidad Nacional de San Agustin con la
equidad educativa.
.PP
.I "Universidad Nacional de San Agustin de Arequipa \(em Curso de Compiladores \(em 2026"
