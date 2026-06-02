# Compilador Accesible — Lenguaje `.acc`

Compilador de dos fases (análisis léxico + análisis sintáctico) para un lenguaje de programación en español natural. Implementado en C++17 con un parser de descenso recursivo hecho a mano.

---

## Tabla de contenidos

- [Descripción](#descripción)
- [Características](#características)
- [Requisitos](#requisitos)
- [Compilar y ejecutar](#compilar-y-ejecutar)
- [Uso del compilador](#uso-del-compilador)
- [Gramática formal](#gramática-formal)
- [El lenguaje `.acc`](#el-lenguaje-acc)
  - [Tipos de datos](#tipos-de-datos)
  - [Declaración de variables](#declaración-de-variables)
  - [Salida por pantalla](#salida-por-pantalla)
  - [Expresiones aritméticas](#expresiones-aritméticas)
  - [Condicionales](#condicionales)
  - [Bucle `repetir`](#bucle-repetir)
  - [Bucle `mientras`](#bucle-mientras)
  - [Condiciones y operadores lógicos](#condiciones-y-operadores-lógicos)
  - [Comentarios](#comentarios)
- [Tablas del compilador](#tablas-del-compilador)
  - [Tabla de palabras clave](#tabla-de-palabras-clave)
  - [Tabla de tipos de token](#tabla-de-tipos-de-token)
  - [Tabla de símbolos](#tabla-de-símbolos)
  - [Tabla de nodos del AST](#tabla-de-nodos-del-ast)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Arquitectura interna](#arquitectura-interna)

---

## Descripción

El **Compilador Accesible** procesa archivos escritos en el lenguaje `.acc`, un lenguaje de programación imperativo cuya sintaxis está diseñada en español. El objetivo es que sea legible y cercano al lenguaje natural, permitiendo aprender conceptos de programación sin la barrera del inglés.

El compilador ejecuta dos fases:

1. **Análisis léxico**: convierte el código fuente en una secuencia de tokens clasificados.
2. **Análisis sintáctico**: valida la estructura gramatical y construye un Árbol de Sintaxis Abstracta (AST).

Los errores se reportan con número de línea, columna y puntero visual al estilo de GCC/Clang.

---

## Características

- Sintaxis completamente en español
- Palabras clave case-insensitive (`Definir` = `definir` = `DEFINIR`)
- Literales numéricos enteros y decimales
- Literales de texto con secuencias de escape (`\n`, `\t`)
- Literales booleanos (`verdadero`, `falso`)
- Expresiones aritméticas con precedencia correcta (`por`/`entre` antes que `mas`/`menos`)
- Condiciones con comparadores en lenguaje natural (`es mayor que`, `es igual a`, etc.)
- Operadores lógicos `y`, `o`, `no`
- Agrupación con paréntesis
- Comentarios de línea con `#`
- Reporte de errores con contexto visual (línea fuente + puntero `^`)
- Modo interactivo (sin archivo)
- Salida con colores ANSI

---

## Requisitos

- `g++` con soporte para C++17 (`-std=c++17`)
- `make`
- Terminal con soporte para colores ANSI (Linux/macOS)

---

## Compilar y ejecutar

```bash
# Compilar
make

# Ejecutar con un archivo
./build/compilador ejemplos/validos/completo.acc

# Ejecutar en modo interactivo (escribe código, línea vacía para terminar)
./build/compilador

# Limpiar los binarios
make clean
```

### Targets de make disponibles

| Target         | Descripción                                                |
|----------------|------------------------------------------------------------|
| `make`         | Compila el proyecto                                        |
| `make run`     | Compila y lanza el modo interactivo                        |
| `make test`    | Ejecuta todos los ejemplos (válidos y con errores)         |
| `make tokens`  | Muestra solo la tabla de tokens del ejemplo `completo.acc` |
| `make ast`     | Muestra solo el AST del ejemplo `completo.acc`             |
| `make check`   | Valida todos los ejemplos en modo silencioso               |
| `make clean`   | Elimina binarios compilados                                |

---

## Uso del compilador

```
./build/compilador [opciones] [archivo.acc]
```

| Opción           | Descripción                                         |
|------------------|-----------------------------------------------------|
| _(ninguna)_      | Ejecuta ambas fases y muestra tabla de tokens + AST |
| `--tokens`, `-t` | Solo muestra la tabla de tokens (fase 1)            |
| `--ast`, `-a`    | Solo muestra el AST (fase 2)                        |
| `--check`, `-c`  | Valida sin mostrar salida detallada                 |
| `--help`, `-h`   | Muestra la ayuda                                    |

**Ejemplos:**

```bash
./build/compilador ejemplos/validos/basico.acc
./build/compilador --tokens ejemplos/validos/completo.acc
./build/compilador --ast    ejemplos/validos/condicion.acc
./build/compilador --check  ejemplos/errores/errores_sint.acc
```

**Código de salida:**

- `0` — compilación exitosa
- `1` — se encontraron errores léxicos o sintácticos

---

## Gramática formal

La gramática está definida en notación BNF extendida (EBNF). Los símbolos terminales aparecen entre comillas; `*` significa cero o más repeticiones; `?` significa opcional; `|` es alternativa.

```ebnf
(* Regla raíz *)
programa        ::= instruccion* EOF

(* Instrucciones *)
instruccion     ::= declaracion
                  | condicional
                  | bucle_repetir
                  | bucle_mientras
                  | mostrar

declaracion     ::= "definir" IDENT "como" expresion

condicional     ::= "si" condicion "entonces" NEWLINE
                        bloque
                    ( "sino" NEWLINE bloque )?
                    "fin" "si"

bucle_repetir   ::= "repetir" expresion "veces" NEWLINE
                        bloque
                    "fin" "repetir"

bucle_mientras  ::= "mientras" condicion NEWLINE
                        bloque
                    "fin" "mientras"

mostrar         ::= "mostrar" expresion

bloque          ::= instruccion*        (* termina ante "fin", "sino" o EOF *)

(* Expresiones aritméticas — precedencia ascendente *)
expresion       ::= termino ( ( "mas" | "menos" ) termino )*
termino         ::= factor  ( ( "por" | "entre" ) factor  )*
factor          ::= NUMERO
                  | TEXTO
                  | "verdadero"
                  | "falso"
                  | IDENT
                  | "(" expresion ")"

(* Condiciones lógicas *)
condicion       ::= "no" condicion_base
                  | condicion_base ( ( "y" | "o" ) condicion_base )*

condicion_base  ::= expresion comparador expresion

comparador      ::= "es" "igual" "a"
                  | "es" "mayor" "que"
                  | "es" "menor" "que"
                  | "es" "mayor" "o" "igual" "que"
                  | "es" "menor" "o" "igual" "que"

(* Tokens terminales *)
IDENT           ::= ( letra | "_" ) ( letra | digito | "_" )*
NUMERO          ::= digito+ ( "." digito+ )?
TEXTO           ::= '"' ( caracter | "\n" | "\t" )* '"'
NEWLINE         ::= "\n"
EOF             ::= <fin de archivo>
```

**Notas sobre la gramática:**

- La **precedencia aritmética** se resuelve mediante la jerarquía `expresion → termino → factor`: `por` y `entre` tienen mayor precedencia que `mas` y `menos`.
- Los **comparadores** son frases de múltiples tokens (`es`, `mayor`, `que`), no símbolos simples.
- Las **condiciones compuestas** con `y`/`o` son asociativas por la izquierda.
- `no` solo puede negar una `condicion_base`, no una condición compuesta entera.
- El lenguaje es **sensible al salto de línea**: `NEWLINE` actúa como separador de instrucciones.

---

## El lenguaje `.acc`

### Tipos de datos

| Tipo      | Ejemplos                              |
|-----------|---------------------------------------|
| Número    | `42`, `3.14`, `0.5`                   |
| Texto     | `"hola mundo"`, `"linea1\nlinea2"`    |
| Booleano  | `verdadero`, `falso`                  |

### Declaración de variables

```
definir <nombre> como <expresion>
```

```acc
definir edad como 20
definir nombre como "Ana"
definir activo como verdadero
definir total como edad mas 5
```

Una variable se puede redefinir en cualquier momento con la misma sintaxis.

### Salida por pantalla

```
mostrar <expresion>
```

```acc
mostrar "Hola, mundo"
mostrar edad
mostrar edad mas 1
```

### Expresiones aritméticas

Las expresiones respetan la precedencia estándar: multiplicación y división antes que suma y resta. Se pueden usar paréntesis para agrupar.

| Operador       | Palabra clave |
|----------------|---------------|
| Suma           | `mas`         |
| Resta          | `menos`       |
| Multiplicación | `por`         |
| División       | `entre`       |

```acc
definir resultado como (3 mas 2) por 4
definir promedio como suma entre total
```

### Condicionales

```
si <condicion> entonces
    <bloque>
[sino
    <bloque>]
fin si
```

```acc
si nota es mayor que 60 entonces
    mostrar "Aprobado"
sino
    mostrar "Desaprobado"
fin si
```

La rama `sino` es opcional.

### Bucle `repetir`

Repite el bloque un número fijo de veces.

```
repetir <expresion> veces
    <bloque>
fin repetir
```

```acc
repetir 5 veces
    mostrar "iteracion"
fin repetir
```

### Bucle `mientras`

Repite el bloque mientras la condición sea verdadera.

```
mientras <condicion>
    <bloque>
fin mientras
```

```acc
definir i como 0
mientras i es menor que 10
    definir i como i mas 1
fin mientras
mostrar i
```

### Condiciones y operadores lógicos

Una condición compara dos expresiones con un comparador en lenguaje natural:

| Comparador              | Equivalente simbólico |
|-------------------------|-----------------------|
| `es igual a`            | `==`                  |
| `es mayor que`          | `>`                   |
| `es menor que`          | `<`                   |
| `es mayor o igual que`  | `>=`                  |
| `es menor o igual que`  | `<=`                  |

Las condiciones se pueden encadenar con operadores lógicos:

| Operador | Palabra clave | Equivalente |
|----------|---------------|-------------|
| AND      | `y`           | `&&`        |
| OR       | `o`           | `\|\|`      |
| NOT      | `no`          | `!`         |

```acc
# Condicion compuesta
si x es mayor que 5 y x es menor que 10 entonces
    mostrar "x esta en rango"
fin si

# Negacion
si no x es igual a 0 entonces
    mostrar "x no es cero"
fin si
```

### Comentarios

Los comentarios de línea comienzan con `#` y se extienden hasta el final de la línea.

```acc
# Esto es un comentario
definir x como 10  # comentario en linea
```

---

## Tablas del compilador

### Tabla de palabras clave

El lexer utiliza una tabla hash (`std::unordered_map<string, TipoToken>`) para el reconocimiento de palabras clave. La búsqueda es **O(1)** y case-insensitive (se normaliza a minúsculas antes de consultar).

| Palabra clave | Token        | Categoría     |
|---------------|--------------|---------------|
| `definir`     | `DEFINIR`    | Declaración   |
| `como`        | `COMO`       | Declaración   |
| `si`          | `SI`         | Condicional   |
| `entonces`    | `ENTONCES`   | Condicional   |
| `sino`        | `SINO`       | Condicional   |
| `fin`         | `FIN`        | Cierre bloque |
| `repetir`     | `REPETIR`    | Bucle         |
| `veces`       | `VECES`      | Bucle         |
| `mientras`    | `MIENTRAS`   | Bucle         |
| `mostrar`     | `MOSTRAR`    | Salida        |
| `mas`         | `MAS`        | Aritmética    |
| `menos`       | `MENOS`      | Aritmética    |
| `por`         | `POR`        | Aritmética    |
| `entre`       | `ENTRE`      | Aritmética    |
| `es`          | `ES`         | Comparador    |
| `mayor`       | `MAYOR`      | Comparador    |
| `menor`       | `MENOR`      | Comparador    |
| `igual`       | `IGUAL`      | Comparador    |
| `que`         | `QUE`        | Comparador    |
| `a`           | `A`          | Comparador    |
| `y`           | `Y`          | Lógico        |
| `o`           | `O`          | Lógico        |
| `no`          | `NO`         | Lógico        |
| `verdadero`   | `VERDADERO`  | Literal bool  |
| `falso`       | `FALSO`      | Literal bool  |

---

### Tabla de tipos de token

El tipo `TipoToken` es un `enum class` que clasifica todos los lexemas posibles. La tabla de tokens producida por el lexer en fase 1 tiene las columnas: **TIPO**, **VALOR**, **LÍNEA**, **COLUMNA**.

| Categoría       | Tipos de token incluidos                                                    | Color en consola |
|-----------------|-----------------------------------------------------------------------------|------------------|
| `keyword`       | `DEFINIR`, `COMO`, `SI`, `ENTONCES`, `SINO`, `FIN`, `REPETIR`, `VECES`, `MIENTRAS`, `MOSTRAR` | Azul  |
| `operador`      | `MAS`, `MENOS`, `POR`, `ENTRE`, `ES`, `MAYOR`, `MENOR`, `IGUAL`, `QUE`, `A`, `Y`, `O`, `NO`  | Amarillo |
| `literal`       | `NUMERO`, `TEXTO`, `VERDADERO`, `FALSO`                                     | Verde            |
| `identificador` | `IDENTIFICADOR`                                                             | Cian             |
| `control`       | `PAREN_IZQ`, `PAREN_DER`, `NUEVA_LINEA`, `FIN_ARCHIVO`                     | Blanco           |
| `error`         | `ERROR`                                                                     | Rojo             |

**Ejemplo de tabla de tokens** para `definir x como 3 mas 2`:

```
+------------------+------------------------+--------+----------+
| TIPO             | VALOR                  | LINEA  | COLUMNA  |
+------------------+------------------------+--------+----------+
| DEFINIR          | definir                | 1      | 1        |
| IDENTIFICADOR    | x                      | 1      | 8        |
| COMO             | como                   | 1      | 10       |
| NUMERO           | 3                      | 1      | 15       |
| MAS              | mas                    | 1      | 17       |
| NUMERO           | 2                      | 1      | 21       |
+------------------+------------------------+--------+----------+
```

---

### Tabla de símbolos

La **tabla de símbolos** almacena información sobre cada identificador declarado en el programa. En la versión actual del compilador (fases 1 y 2) se construye implícitamente durante el análisis sintáctico: cada nodo `NodoDeclaracion` del AST registra el nombre de la variable y su expresión de inicialización.

Cada entrada en la tabla de símbolos contiene:

| Campo        | Tipo       | Descripción                                      |
|--------------|------------|--------------------------------------------------|
| `nombre`     | `string`   | Identificador tal como aparece en el código      |
| `expresion`  | `NodoPtr`  | Subárbol AST con el valor asignado               |
| `linea`      | `int`      | Línea donde fue declarada (registrada en el token) |
| `columna`    | `int`      | Columna de inicio del identificador              |

**Ejemplo**: para el programa:

```acc
definir base como 5
definir altura como base mas 3
```

La tabla de símbolos quedaría:

| Nombre    | Expresión                | Línea | Columna |
|-----------|--------------------------|-------|---------|
| `base`    | `Numero(5)`              | 1     | 8       |
| `altura`  | `OpBinaria[mas](base, 3)`| 2     | 8       |

> **Nota:** La resolución de valores y la detección de variables no declaradas corresponde a la fase de **análisis semántico**, que es la siguiente fase a implementar en el compilador.

---

### Tabla de nodos del AST

El AST se construye con `std::unique_ptr` para gestión automática de memoria. Todos los nodos heredan de la clase base abstracta `Nodo`.

#### Nodos de expresión

| Nodo               | Campos principales                          | Representa                              |
|--------------------|---------------------------------------------|-----------------------------------------|
| `NodoNumero`       | `double valor`                              | Literal numérico: `42`, `3.14`          |
| `NodoTexto`        | `string valor`                              | Literal de texto: `"hola"`              |
| `NodoBooleano`     | `bool valor`                                | `verdadero` / `falso`                   |
| `NodoIdentificador`| `string nombre`                             | Variable: `x`, `contador`              |
| `NodoOpBinaria`    | `NodoPtr izq`, `string op`, `NodoPtr der`   | `a mas b`, `x por y`                   |

#### Nodos de condición

| Nodo              | Campos principales                          | Representa                              |
|-------------------|---------------------------------------------|-----------------------------------------|
| `NodoComparacion` | `NodoPtr izq`, `string comp`, `NodoPtr der` | `x es mayor que 5`                      |
| `NodoOpLogica`    | `NodoPtr izq`, `string op`, `NodoPtr der`   | `cond1 y cond2`, `cond1 o cond2`        |
| `NodoNegar`       | `NodoPtr operando`                          | `no condicion`                          |

#### Nodos de instrucción

| Nodo                | Campos principales                                         | Representa                       |
|---------------------|------------------------------------------------------------|----------------------------------|
| `NodoDeclaracion`   | `string nombre`, `NodoPtr expresion`                       | `definir x como ...`             |
| `NodoCondicional`   | `NodoPtr condicion`, `vector entonces`, `vector sino`      | `si ... entonces ... fin si`     |
| `NodoBucleRepetir`  | `NodoPtr veces`, `vector cuerpo`                           | `repetir N veces ... fin repetir`|
| `NodoBucleMientras` | `NodoPtr condicion`, `vector cuerpo`                       | `mientras ... fin mientras`      |
| `NodoMostrar`       | `NodoPtr expresion`                                        | `mostrar ...`                    |
| `NodoPrograma`      | `vector<NodoPtr> instrucciones`                            | Raíz del árbol completo          |

**Ejemplo de AST** para `si x es mayor que 5 entonces mostrar x fin si`:

```
Programa
└── Condicional
    ├── Comparacion [es mayor que]
    │   ├── Identificador (x)
    │   └── Numero (5)
    └── Entonces
        └── Mostrar
            └── Identificador (x)
```

---

## Estructura del proyecto

```
PROJECT_COMP/
├── src/
│   ├── token.hpp / token.cpp       # Definición y métodos del tipo Token
│   ├── lexer.hpp  / lexer.cpp      # Analizador léxico + tabla de palabras clave
│   ├── ast.hpp    / ast.cpp        # Nodos del AST e impresión visual
│   ├── parser.hpp / parser.cpp     # Parser de descenso recursivo
│   └── main.cpp                    # Punto de entrada, CLI y reporte
├── ejemplos/
│   ├── validos/
│   │   ├── basico.acc              # Declaraciones y bucle simple
│   │   ├── condicion.acc           # Condicionales y lógica
│   │   └── completo.acc            # Uso de todas las estructuras
│   └── errores/
│       ├── errores_lex.acc         # Errores léxicos intencionales
│       └── errores_sint.acc        # Errores sintácticos intencionales
├── docs/
│   └── documentacion.ms / .pdf    # Documentación formal del proyecto
├── build/                          # Binarios compilados (generado por make)
├── Makefile
└── README.md
```

---

## Arquitectura interna

El compilador sigue una arquitectura de pipeline clásica de dos etapas:

```
Código fuente (.acc)
        │
        ▼
┌───────────────────────────────────────────────────┐
│  FASE 1 — ANÁLISIS LÉXICO  (lexer.cpp)            │
│                                                    │
│  fuente  ──►  Lexer::tokenizar()  ──►  tokens[]   │
│                                                    │
│  Tabla usada: PALABRAS_CLAVE (unordered_map)       │
│  Salida: std::vector<Token>                        │
└──────────────────────┬────────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────────┐
│  FASE 2 — ANÁLISIS SINTÁCTICO  (parser.cpp)       │
│                                                    │
│  tokens[]  ──►  Parser::parsear()  ──►  AST       │
│                                                    │
│  Tabla usada: Tabla de símbolos (NodoDeclaracion) │
│  Salida: std::unique_ptr<NodoPrograma>             │
└──────────────────────┬────────────────────────────┘
                       │
                       ▼
        AST impreso + Reporte de compilación
```

### Lexer

- Recorre el código fuente carácter a carácter.
- Clasifica palabras clave, identificadores, números, cadenas de texto y paréntesis.
- Emite `NUEVA_LINEA` como token significativo (el parser lo usa como separador de instrucciones).
- Registra errores sin detener el análisis (recuperación de errores).
- Reconocimiento de palabras clave es **case-insensitive**.

### Parser

- Parser de **descenso recursivo** manual, sin generadores de parsers.
- Cada regla gramatical tiene su propia función (`parsearDeclaracion`, `parsearCondicional`, etc.).
- La precedencia aritmética se implementa mediante la jerarquía `expresion → termino → factor`.
- Recuperación de errores: al encontrar un error en una instrucción, consume hasta el fin de línea y continúa con la siguiente.

### AST

- Árbol de punteros únicos (`std::unique_ptr`) con gestión automática de memoria.
- Cada nodo implementa `imprimir()` para mostrar el árbol con conectores visuales (`├──`, `└──`).
- Los nodos de instrucción contienen vectores de hijos para los bloques anidados.
