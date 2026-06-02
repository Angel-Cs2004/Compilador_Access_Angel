#include "generador.hpp"
#include <sstream>
#include <cmath>

// -----------------------------------------------------------------------
// Utilidades
// -----------------------------------------------------------------------
void GeneradorPython::sangrar() {
    for (int i = 0; i < sangria_; i++) ss_ << "    ";
}

// -----------------------------------------------------------------------
// Punto de entrada
// -----------------------------------------------------------------------
std::string GeneradorPython::generar(const NodoPrograma& programa) {
    ss_.str("");
    ss_.clear();
    sangria_ = 0;

    ss_ << "# Generado por Compilador Accesible v0.4\n";
    ss_ << "# Lenguaje .acc -> Python 3\n\n";

    generarBloque(programa.instrucciones);
    return ss_.str();
}

void GeneradorPython::generarBloque(const std::vector<NodoPtr>& bloque) {
    for (const auto& n : bloque)
        if (n) generarInstruccion(*n);
}

// -----------------------------------------------------------------------
// Instrucciones
// -----------------------------------------------------------------------
void GeneradorPython::generarInstruccion(const Nodo& nodo) {

    if (auto* decl = dynamic_cast<const NodoDeclaracion*>(&nodo)) {
        sangrar();
        ss_ << decl->nombre << " = " << generarExpresion(*decl->expresion) << "\n";
        return;
    }

    if (auto* most = dynamic_cast<const NodoMostrar*>(&nodo)) {
        sangrar();
        ss_ << "print(" << generarExpresion(*most->expresion) << ")\n";
        return;
    }

    if (auto* cond = dynamic_cast<const NodoCondicional*>(&nodo)) {
        sangrar();
        ss_ << "if " << generarCondicion(*cond->condicion) << ":\n";
        sangria_++;
        if (cond->entonces.empty()) { sangrar(); ss_ << "pass\n"; }
        else generarBloque(cond->entonces);
        sangria_--;
        if (!cond->sino.empty()) {
            sangrar(); ss_ << "else:\n";
            sangria_++;
            generarBloque(cond->sino);
            sangria_--;
        }
        return;
    }

    if (auto* rep = dynamic_cast<const NodoBucleRepetir*>(&nodo)) {
        sangrar();
        ss_ << "for _i in range(" << generarExpresion(*rep->veces) << "):\n";
        sangria_++;
        if (rep->cuerpo.empty()) { sangrar(); ss_ << "pass\n"; }
        else generarBloque(rep->cuerpo);
        sangria_--;
        return;
    }

    if (auto* mien = dynamic_cast<const NodoBucleMientras*>(&nodo)) {
        sangrar();
        ss_ << "while " << generarCondicion(*mien->condicion) << ":\n";
        sangria_++;
        if (mien->cuerpo.empty()) { sangrar(); ss_ << "pass\n"; }
        else generarBloque(mien->cuerpo);
        sangria_--;
        return;
    }
}

// -----------------------------------------------------------------------
// Expresiones aritmeticas
// -----------------------------------------------------------------------
std::string GeneradorPython::generarExpresion(const Nodo& nodo) {

    if (auto* num = dynamic_cast<const NodoNumero*>(&nodo)) {
        std::ostringstream ss;
        long long vi = static_cast<long long>(num->valor);
        if (static_cast<double>(vi) == num->valor) ss << vi;
        else                                        ss << num->valor;
        return ss.str();
    }

    if (auto* txt = dynamic_cast<const NodoTexto*>(&nodo)) {
        std::string r = "\"";
        for (char c : txt->valor) {
            if      (c == '"')  r += "\\\"";
            else if (c == '\\') r += "\\\\";
            else if (c == '\n') r += "\\n";
            else if (c == '\t') r += "\\t";
            else                r += c;
        }
        r += "\"";
        return r;
    }

    if (auto* bol = dynamic_cast<const NodoBooleano*>(&nodo)) {
        return bol->valor ? "True" : "False";
    }

    if (auto* id = dynamic_cast<const NodoIdentificador*>(&nodo)) {
        return id->nombre;
    }

    if (auto* op = dynamic_cast<const NodoOpBinaria*>(&nodo)) {
        std::string izq = generarExpresion(*op->izquierda);
        std::string der = generarExpresion(*op->derecha);
        std::string sym;
        if      (op->operador == "mas")   sym = " + ";
        else if (op->operador == "menos") sym = " - ";
        else if (op->operador == "por")   sym = " * ";
        else if (op->operador == "entre") sym = " / ";
        else                              sym = " " + op->operador + " ";
        return "(" + izq + sym + der + ")";
    }

    return generarCondicion(nodo);
}

// -----------------------------------------------------------------------
// Condiciones
// -----------------------------------------------------------------------
std::string GeneradorPython::generarCondicion(const Nodo& nodo) {

    if (auto* comp = dynamic_cast<const NodoComparacion*>(&nodo)) {
        std::string izq = generarExpresion(*comp->izquierda);
        std::string der = generarExpresion(*comp->derecha);
        std::string sym;
        if      (comp->comparador == "es igual a")          sym = " == ";
        else if (comp->comparador == "es mayor que")         sym = " > ";
        else if (comp->comparador == "es menor que")         sym = " < ";
        else if (comp->comparador == "es mayor o igual que") sym = " >= ";
        else if (comp->comparador == "es menor o igual que") sym = " <= ";
        else                                                  sym = " ? ";
        return izq + sym + der;
    }

    if (auto* oplog = dynamic_cast<const NodoOpLogica*>(&nodo)) {
        std::string izq = generarCondicion(*oplog->izquierda);
        std::string der = generarCondicion(*oplog->derecha);
        std::string sym = (oplog->operador == "y") ? " and " : " or ";
        return "(" + izq + sym + der + ")";
    }

    if (auto* neg = dynamic_cast<const NodoNegar*>(&nodo)) {
        return "not " + generarCondicion(*neg->operando);
    }

    return "False";
}
