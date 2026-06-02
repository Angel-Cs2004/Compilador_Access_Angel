#pragma once
#include "codintermedio.hpp"
#include <vector>
#include <string>

// -----------------------------------------------------------------------
// Optimizador — aplica pasadas de optimizacion al codigo intermedio
//
// Pasadas implementadas:
//   1. Plegado de constantes (constant folding): evalua operaciones sobre
//      literales numericos/booleanos en tiempo de compilacion.
//   2. Propagacion de constantes (constant propagation): sustituye usos
//      de temporales cuyo valor es conocido y constante.
//   3. Eliminacion de codigo muerto: descarta asignaciones a temporales
//      que nunca son leidos despues.
// -----------------------------------------------------------------------
class Optimizador {
public:
    std::vector<InstrIR> optimizar(std::vector<InstrIR> codigo);

    int instruccionesEliminadas() const { return eliminadas_; }

private:
    int eliminadas_ = 0;

    std::vector<InstrIR> plegarConstantes(std::vector<InstrIR> codigo);
    std::vector<InstrIR> propagarConstantes(std::vector<InstrIR> codigo);
    std::vector<InstrIR> eliminarMuertos(std::vector<InstrIR> codigo);

    static bool   esConstanteNumerica(const std::string& s, double& valor);
    static bool   esConstanteBooleana(const std::string& s, bool& valor);
    static bool   esConstante(const std::string& s);
    static bool   esTemporal(const std::string& s);
    static std::string numToStr(double v);
};
