# Compilador Accesible — Lenguaje `.acc`

Compilador de dos fases (análisis léxico + análisis sintáctico) para un lenguaje de programación en español natural. Implementado en C++17 con un parser de descenso recursivo hecho a mano.

---

## Tabla de contenidos

- [Descripción](#descripción)
- [Características](#características)
- [Requisitos](#requisitos)
- [Compilar y ejecutar](#compilar-y-ejecutar)
- [Uso del compilador](#uso-del-compilador)
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

| Target       | Descripción                                               |
|--------------|-----------------------------------------------------------|
| `make`       | Compila el proyecto                                       |
| `make run`   | Compila y lanza el modo interactivo                       |
| `make test`  | Ejecuta todos los ejemplos (válidos y con errores)        |
| `make tokens`| Muestra solo la tabla de tokens del ejemplo `completo.acc`|
| `make ast`   | Muestra solo el AST del ejemplo `completo.acc`            |
| `make check` | Valida todos los ejemplos en modo silencioso              |
| `make clean` | Elimina binarios compilados                               |

---

## Uso del compilador

```
./build/compilador [opciones] [archivo.acc]
```

| Opción          | Descripción                                        |
|-----------------|----------------------------------------------------|
| _(ninguna)_     | Ejecuta ambas fases y muestra tabla de tokens + AST|
| `--tokens`, `-t`| Solo muestra la tabla de tokens (fase 1)           |
| `--ast`, `-a`   | Solo muestra el AST (fase 2)                       |
| `--check`, `-c` | Valida sin mostrar salida detallada                |
| `--help`, `-h`  | Muestra la ayuda                                   |

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

## El lenguaje `.acc`

### Tipos de datos

| Tipo      | Ejemplos                        |
|-----------|---------------------------------|
| Número    | `42`, `3.14`, `0.5`             |
| Texto     | `"hola mundo"`, `"linea1\nlinea2"` |
| Booleano  | `verdadero`, `falso`            |

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

| Operador | Palabra clave |
|----------|--------------|
| Suma     | `mas`        |
| Resta    | `menos`      |
| Multiplicación | `por`  |
| División | `entre`      |

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

| Comparador              | Significado  |
|-------------------------|--------------|
| `es igual a`            | `==`         |
| `es mayor que`          | `>`          |
| `es menor que`          | `<`          |
| `es mayor o igual que`  | `>=`         |
| `es menor o igual que`  | `<=`         |

Las condiciones se pueden encadenar con operadores lógicos:

| Operador | Palabra clave |
|----------|--------------|
| AND      | `y`          |
| OR       | `o`          |
| NOT      | `no`         |

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

## Estructura del proyecto

```
PROJECT_COMP/
├── src/
│   ├── token.hpp / token.cpp      # Definición y métodos del tipo Token
│   ├── lexer.hpp  / lexer.cpp     # Analizador léxico
│   ├── ast.hpp    / ast.cpp       # Nodos del AST e impresión
│   ├── parser.hpp / parser.cpp    # Parser de descenso recursivo
│   └── main.cpp                   # Punto de entrada, CLI y reporte
├── ejemplos/
│   ├── validos/
│   │   ├── basico.acc             # Declaraciones y bucle simple
│   │   ├── condicion.acc          # Condicionales y lógica
│   │   └── completo.acc           # Uso de todas las estructuras
│   └── errores/
│       ├── errores_lex.acc        # Errores léxicos intencionales
│       └── errores_sint.acc       # Errores sintácticos intencionales
├── docs/
│   └── documentacion.ms / .pdf   # Documentación formal del proyecto
├── build/                         # Binarios compilados (generado por make)
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
┌───────────────┐
│     LEXER     │  Convierte caracteres → tokens clasificados
└───────┬───────┘
        │  std::vector<Token>
        ▼
┌───────────────┐
│    PARSER     │  Valida gramática → construye el AST
└───────┬───────┘
        │  std::unique_ptr<NodoPrograma>
        ▼
   AST impreso + Reporte de compilación
```

### Lexer (`lexer.cpp`)

- Recorre el código fuente carácter a carácter.
- Clasifica palabras clave, identificadores, números, cadenas de texto y paréntesis.
- Emite `NUEVA_LINEA` como token significativo (el parser lo usa como separador de instrucciones).
- Registra errores sin detener el análisis (recuperación de errores).
- Reconocimiento de palabras clave es **case-insensitive**.

### Parser (`parser.cpp`)

- Parser de **descenso recursivo** manual, sin generadores de parsers.
- Cada regla gramatical tiene su propia función (`parsearDeclaracion`, `parsearCondicional`, etc.).
- La precedencia aritmética se implementa mediante la jerarquía `expresion → termino → factor`.
- Recuperación de errores: al encontrar un error en una instrucción, consume hasta el fin de línea y continúa con la siguiente.

### AST (`ast.cpp`)

Nodos implementados:

| Nodo              | Corresponde a           |
|-------------------|-------------------------|
| `NodoPrograma`    | Raíz del árbol          |
| `NodoDeclaracion` | `definir x como ...`    |
| `NodoCondicional` | `si ... entonces ... fin si` |
| `NodoBucleRepetir`| `repetir N veces ... fin repetir` |
| `NodoBucleMientras`| `mientras ... fin mientras` |
| `NodoMostrar`     | `mostrar ...`           |
| `NodoOpBinaria`   | Operaciones `+`, `-`, `*`, `/` |
| `NodoOpLogica`    | `y`, `o`                |
| `NodoComparacion` | `es mayor que`, etc.    |
| `NodoNegar`       | `no`                    |
| `NodoNumero`      | Literal numérico        |
| `NodoTexto`       | Literal de texto        |
| `NodoBooleano`    | `verdadero`, `falso`    |
| `NodoIdentificador`| Nombre de variable     |
