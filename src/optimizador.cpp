#include "optimizador.hpp"
#include <sstream>
#include <unordered_map>
#include <unordered_set>

// -----------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------
bool Optimizador::esConstanteNumerica(const std::string& s, double& valor) {
    if (s.empty()) return false;
    try {
        size_t pos = 0;
        valor = std::stod(s, &pos);
        return pos == s.size();
    } catch (...) { return false; }
}

bool Optimizador::esConstanteBooleana(const std::string& s, bool& valor) {
    if (s == "verdadero") { valor = true;  return true; }
    if (s == "falso")     { valor = false; return true; }
    return false;
}

bool Optimizador::esConstante(const std::string& s) {
    if (s.empty()) return false;
    double d; bool b;
    if (esConstanteNumerica(s, d))  return true;
    if (esConstanteBooleana(s, b))  return true;
    return s.size() >= 2 && s.front() == '"' && s.back() == '"';
}

bool Optimizador::esTemporal(const std::string& s) {
    return !s.empty() && s[0] == '_';
}

std::string Optimizador::numToStr(double v) {
    std::ostringstream ss;
    long long vi = static_cast<long long>(v);
    if (static_cast<double>(vi) == v) ss << vi;
    else                              ss << v;
    return ss.str();
}

// -----------------------------------------------------------------------
// Punto de entrada: aplica todas las pasadas en orden
// -----------------------------------------------------------------------
std::vector<InstrIR> Optimizador::optimizar(std::vector<InstrIR> codigo) {
    size_t antes = codigo.size();
    codigo = plegarConstantes(std::move(codigo));
    codigo = propagarConstantes(std::move(codigo));
    codigo = eliminarMuertos(std::move(codigo));
    eliminadas_ = static_cast<int>(antes - codigo.size());
    return codigo;
}

// -----------------------------------------------------------------------
// Pasada 1: Plegado de constantes
// -----------------------------------------------------------------------
std::vector<InstrIR> Optimizador::plegarConstantes(std::vector<InstrIR> codigo) {
    for (auto& ins : codigo) {
        if (ins.tipo != TipoInstrIR::OP_BIN) continue;

        double a = 0, b = 0;
        bool   ba = false, bb = false;
        bool numA = esConstanteNumerica(ins.arg1, a);
        bool numB = esConstanteNumerica(ins.arg2, b);
        bool bolA = esConstanteBooleana(ins.arg1, ba);
        bool bolB = esConstanteBooleana(ins.arg2, bb);

        auto colapsar = [&](const std::string& val) {
            ins.tipo     = TipoInstrIR::ASIGNAR;
            ins.arg1     = val;
            ins.arg2     = "";
            ins.operador = "";
        };

        if (numA && numB) {
            const std::string& op = ins.operador;
            if      (op == "+")  { colapsar(numToStr(a + b)); continue; }
            else if (op == "-")  { colapsar(numToStr(a - b)); continue; }
            else if (op == "*")  { colapsar(numToStr(a * b)); continue; }
            else if (op == "/" && b != 0) { colapsar(numToStr(a / b)); continue; }
            else if (op == "==") { colapsar((a == b) ? "verdadero" : "falso"); continue; }
            else if (op == ">")  { colapsar((a >  b) ? "verdadero" : "falso"); continue; }
            else if (op == "<")  { colapsar((a <  b) ? "verdadero" : "falso"); continue; }
            else if (op == ">=") { colapsar((a >= b) ? "verdadero" : "falso"); continue; }
            else if (op == "<=") { colapsar((a <= b) ? "verdadero" : "falso"); continue; }
        }

        if (bolA && bolB) {
            const std::string& op = ins.operador;
            if      (op == "&&") { colapsar((ba && bb) ? "verdadero" : "falso"); continue; }
            else if (op == "||") { colapsar((ba || bb) ? "verdadero" : "falso"); continue; }
        }

        // Identidades algebraicas neutras
        if (numB) {
            if ((ins.operador == "+" || ins.operador == "-") && b == 0)
                { colapsar(ins.arg1); continue; }
            if ((ins.operador == "*" || ins.operador == "/") && b == 1)
                { colapsar(ins.arg1); continue; }
            if (ins.operador == "*" && b == 0)
                { colapsar("0"); continue; }
        }
        if (numA && a == 0 && ins.operador == "+")
            { colapsar(ins.arg2); continue; }
        if (numA && a == 1 && ins.operador == "*")
            { colapsar(ins.arg2); continue; }
    }
    return codigo;
}

// -----------------------------------------------------------------------
// Pasada 2: Propagacion de constantes
// -----------------------------------------------------------------------
std::vector<InstrIR> Optimizador::propagarConstantes(std::vector<InstrIR> codigo) {
    std::unordered_map<std::string, std::string> consts;

    for (auto& ins : codigo) {
        // Una etiqueta invalida las constantes previas (puede haber saltos)
        if (ins.tipo == TipoInstrIR::ETIQUETA) { consts.clear(); continue; }

        auto reemplazar = [&](std::string& s) {
            auto it = consts.find(s);
            if (it != consts.end()) s = it->second;
        };
        reemplazar(ins.arg1);
        reemplazar(ins.arg2);

        // Registrar nueva constante en temporal
        if (ins.tipo == TipoInstrIR::ASIGNAR
            && esTemporal(ins.resultado)
            && esConstante(ins.arg1)) {
            consts[ins.resultado] = ins.arg1;
        } else if (!ins.resultado.empty()) {
            consts.erase(ins.resultado);
        }
    }
    return codigo;
}

// -----------------------------------------------------------------------
// Pasada 3: Eliminacion de codigo muerto
// Solo elimina asignaciones a temporales (_tN) que nunca son leidos
// -----------------------------------------------------------------------
std::vector<InstrIR> Optimizador::eliminarMuertos(std::vector<InstrIR> codigo) {
    // Recopila todos los valores que aparecen como argumentos
    std::unordered_set<std::string> usados;
    for (const auto& ins : codigo) {
        if (!ins.arg1.empty())    usados.insert(ins.arg1);
        if (!ins.arg2.empty())    usados.insert(ins.arg2);
        if (!ins.etiqueta.empty()) usados.insert(ins.etiqueta);
    }

    std::vector<InstrIR> resultado;
    resultado.reserve(codigo.size());
    for (const auto& ins : codigo) {
        bool esTmp  = esTemporal(ins.resultado);
        bool usada  = usados.count(ins.resultado) > 0;
        bool muerta = esTmp && !usada
                   && (ins.tipo == TipoInstrIR::ASIGNAR
                       || ins.tipo == TipoInstrIR::OP_BIN
                       || ins.tipo == TipoInstrIR::NEGACION_LOGICA);
        if (!muerta) resultado.push_back(ins);
    }
    return resultado;
}
