#pragma once
#include "ast.hpp"
#include <string>
#include <sstream>

// -----------------------------------------------------------------------
// GeneradorPython — traduce el AST a codigo Python valido y ejecutable
//
// Objetivo: interoperabilidad real con un lenguaje de proposito general
// (descrito en el PDF como requisito del compilador accesible).
// -----------------------------------------------------------------------
class GeneradorPython {
public:
    std::string generar(const NodoPrograma& programa);

private:
    std::ostringstream ss_;
    int sangria_ = 0;

    void sangrar();
    void generarBloque(const std::vector<NodoPtr>& bloque);
    void generarInstruccion(const Nodo& nodo);
    std::string generarExpresion(const Nodo& nodo);
    std::string generarCondicion(const Nodo& nodo);
};
