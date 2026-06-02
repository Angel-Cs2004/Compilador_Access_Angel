#pragma once
#include "ast.hpp"
#include <string>
#include <vector>

// Tipos de instruccion en el codigo intermedio (TAC — Three-Address Code)
enum class TipoInstrIR {
    ASIGNAR,         // resultado = arg1
    OP_BIN,          // resultado = arg1 operador arg2
    NEGACION_LOGICA, // resultado = !arg1
    ETIQUETA,        // etiqueta:
    SALTO,           // goto etiqueta
    SALTO_SI_FALSO,  // if not arg1 goto etiqueta
    MOSTRAR,         // print(arg1)
};

struct InstrIR {
    TipoInstrIR tipo      = TipoInstrIR::ASIGNAR;
    std::string resultado = {};
    std::string arg1      = {};
    std::string operador  = {};
    std::string arg2      = {};
    std::string etiqueta  = {};
    int         linea     = -1;
};

// -----------------------------------------------------------------------
// GeneradorIR — recorre el AST y produce codigo intermedio (TAC)
// -----------------------------------------------------------------------
class GeneradorIR {
public:
    std::vector<InstrIR> generar(const NodoPrograma& programa);

    static void imprimir(const std::vector<InstrIR>& codigo);

private:
    std::vector<InstrIR> codigo_;
    int contadorTemp_ = 0;
    int contadorEtiq_ = 0;

    std::string nuevaTemporal();
    std::string nuevaEtiqueta(const std::string& prefijo = "L");

    void        generarInstruccion(const Nodo& nodo);
    void        generarBloque(const std::vector<NodoPtr>& bloque);
    std::string generarExpresion(const Nodo& nodo);
    std::string generarCondicion(const Nodo& nodo);

    void emitir(InstrIR instr);
};
