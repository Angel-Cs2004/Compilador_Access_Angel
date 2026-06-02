#pragma once
#include "ast.hpp"
#include <string>
#include <vector>
#include <unordered_map>

// Tipos posibles de una expresion en el lenguaje .acc
enum class TipoValor { NUMERO, TEXTO, BOOLEANO, DESCONOCIDO };

std::string nombreTipo(TipoValor t);

// Entrada en la tabla de simbolos
struct InfoVariable {
    TipoValor tipo;
    int       linea;
    int       columna;
};

// -----------------------------------------------------------------------
// AnalizadorSemantico — Fase 3 del compilador
//
// Verifica sobre el AST:
//   1. Variable usada antes de ser declarada
//   2. Redeclaracion de una variable (advertencia, no error)
//   3. Operacion aritmetica con operandos no numericos
//   4. Cantidad de repeticiones no numerica en 'repetir N veces'
//   5. Comparacion entre tipos incompatibles
// -----------------------------------------------------------------------
class AnalizadorSemantico {
public:
    // Punto de entrada: analiza el programa completo
    void analizar(const NodoPrograma& programa);

    bool tieneErrores()      const;
    bool tieneAdvertencias() const;
    const std::vector<std::string>& errores()      const;
    const std::vector<std::string>& advertencias() const;

private:
    std::unordered_map<std::string, InfoVariable> tabla_;   // tabla de simbolos
    std::vector<std::string> errores_;
    std::vector<std::string> advertencias_;

    void      analizarBloque(const std::vector<NodoPtr>& bloque);
    void      analizarInstruccion(const Nodo& nodo);
    TipoValor analizarExpresion(const Nodo& nodo);
    void      analizarCondicion(const Nodo& nodo);

    void registrarError(const std::string& msg, int linea = -1, int columna = -1);
    void registrarAdvertencia(const std::string& msg, int linea = -1, int columna = -1);
};
