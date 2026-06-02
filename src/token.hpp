#pragma once
#include <string>

enum class TipoToken {
    // Declaracion
    DEFINIR, COMO,
    // Condicional
    SI, ENTONCES, SINO, FIN,
    // Bucle for
    REPETIR, VECES,
    // Bucle while
    MIENTRAS,
    // Salida
    MOSTRAR,
    // Aritmetica
    MAS, MENOS, POR, ENTRE,
    // Comparadores
    ES, MAYOR, MENOR, IGUAL, QUE, A,
    // Logicos
    Y, O, NO,
    // Literales
    NUMERO, TEXTO, VERDADERO, FALSO,
    // Identificador de usuario
    IDENTIFICADOR,
    // Agrupacion
    PAREN_IZQ, PAREN_DER,
    // Control de flujo del lexer
    NUEVA_LINEA,
    FIN_ARCHIVO,
    // Caracter no reconocido
    ERROR
};

struct Token {
    TipoToken   tipo;
    std::string valor;
    int         linea;
    int         columna;

    Token(TipoToken tipo, std::string valor, int linea, int columna);
    std::string nombreTipo()     const;
    std::string categoriaColor() const; // para la salida por consola
};
