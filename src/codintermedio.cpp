#include "codintermedio.hpp"
#include <iostream>
#include <iomanip>
#include <sstream>

// -----------------------------------------------------------------------
// Utilidades internas
// -----------------------------------------------------------------------
std::string GeneradorIR::nuevaTemporal() {
    return "_t" + std::to_string(contadorTemp_++);
}

std::string GeneradorIR::nuevaEtiqueta(const std::string& prefijo) {
    return prefijo + std::to_string(contadorEtiq_++);
}

void GeneradorIR::emitir(InstrIR instr) {
    codigo_.push_back(std::move(instr));
}

// -----------------------------------------------------------------------
// Punto de entrada
// -----------------------------------------------------------------------
std::vector<InstrIR> GeneradorIR::generar(const NodoPrograma& programa) {
    codigo_.clear();
    contadorTemp_ = 0;
    contadorEtiq_ = 0;
    generarBloque(programa.instrucciones);
    return codigo_;
}

void GeneradorIR::generarBloque(const std::vector<NodoPtr>& bloque) {
    for (const auto& n : bloque)
        if (n) generarInstruccion(*n);
}

// -----------------------------------------------------------------------
// Instrucciones
// -----------------------------------------------------------------------
void GeneradorIR::generarInstruccion(const Nodo& nodo) {

    if (auto* decl = dynamic_cast<const NodoDeclaracion*>(&nodo)) {
        std::string src = generarExpresion(*decl->expresion);
        emitir({TipoInstrIR::ASIGNAR, decl->nombre, src, "", "", "", decl->linea});
        return;
    }

    if (auto* most = dynamic_cast<const NodoMostrar*>(&nodo)) {
        std::string src = generarExpresion(*most->expresion);
        emitir({TipoInstrIR::MOSTRAR, "", src, "", "", "", most->linea});
        return;
    }

    if (auto* cond = dynamic_cast<const NodoCondicional*>(&nodo)) {
        bool tieneSino = !cond->sino.empty();
        std::string etFalso = nuevaEtiqueta("si_falso_");
        std::string etFin   = tieneSino ? nuevaEtiqueta("si_fin_") : etFalso;

        std::string condTemp = generarCondicion(*cond->condicion);
        emitir({TipoInstrIR::SALTO_SI_FALSO, "", condTemp, "", "", etFalso, cond->linea});
        generarBloque(cond->entonces);

        if (tieneSino) {
            emitir({TipoInstrIR::SALTO, "", "", "", "", etFin});
            emitir({TipoInstrIR::ETIQUETA, "", "", "", "", etFalso});
            generarBloque(cond->sino);
        }
        emitir({TipoInstrIR::ETIQUETA, "", "", "", "", etFin});
        return;
    }

    if (auto* rep = dynamic_cast<const NodoBucleRepetir*>(&nodo)) {
        std::string vecesVal = generarExpresion(*rep->veces);
        std::string contador = nuevaTemporal();
        std::string etIni    = nuevaEtiqueta("rep_ini_");
        std::string etFin    = nuevaEtiqueta("rep_fin_");

        emitir({TipoInstrIR::ASIGNAR, contador, "0", "", "", "", rep->linea});
        emitir({TipoInstrIR::ETIQUETA, "", "", "", "", etIni});

        std::string condTemp = nuevaTemporal();
        emitir({TipoInstrIR::OP_BIN, condTemp, contador, "<", vecesVal});
        emitir({TipoInstrIR::SALTO_SI_FALSO, "", condTemp, "", "", etFin});

        generarBloque(rep->cuerpo);

        std::string incr = nuevaTemporal();
        emitir({TipoInstrIR::OP_BIN, incr, contador, "+", "1"});
        emitir({TipoInstrIR::ASIGNAR, contador, incr});
        emitir({TipoInstrIR::SALTO, "", "", "", "", etIni});
        emitir({TipoInstrIR::ETIQUETA, "", "", "", "", etFin});
        return;
    }

    if (auto* mien = dynamic_cast<const NodoBucleMientras*>(&nodo)) {
        std::string etIni = nuevaEtiqueta("mien_ini_");
        std::string etFin = nuevaEtiqueta("mien_fin_");

        emitir({TipoInstrIR::ETIQUETA, "", "", "", "", etIni});
        std::string condTemp = generarCondicion(*mien->condicion);
        emitir({TipoInstrIR::SALTO_SI_FALSO, "", condTemp, "", "", etFin});
        generarBloque(mien->cuerpo);
        emitir({TipoInstrIR::SALTO, "", "", "", "", etIni});
        emitir({TipoInstrIR::ETIQUETA, "", "", "", "", etFin});
        return;
    }
}

// -----------------------------------------------------------------------
// Expresiones: retorna el nombre del temporal/literal con el resultado
// -----------------------------------------------------------------------
std::string GeneradorIR::generarExpresion(const Nodo& nodo) {

    if (auto* num = dynamic_cast<const NodoNumero*>(&nodo)) {
        std::ostringstream ss;
        if (num->valor == static_cast<long long>(num->valor))
            ss << static_cast<long long>(num->valor);
        else
            ss << num->valor;
        return ss.str();
    }

    if (auto* txt = dynamic_cast<const NodoTexto*>(&nodo)) {
        return "\"" + txt->valor + "\"";
    }

    if (auto* bol = dynamic_cast<const NodoBooleano*>(&nodo)) {
        return bol->valor ? "verdadero" : "falso";
    }

    if (auto* id = dynamic_cast<const NodoIdentificador*>(&nodo)) {
        return id->nombre;
    }

    if (auto* op = dynamic_cast<const NodoOpBinaria*>(&nodo)) {
        std::string izq = generarExpresion(*op->izquierda);
        std::string der = generarExpresion(*op->derecha);
        std::string sym;
        if      (op->operador == "mas")   sym = "+";
        else if (op->operador == "menos") sym = "-";
        else if (op->operador == "por")   sym = "*";
        else if (op->operador == "entre") sym = "/";
        else                              sym = op->operador;
        std::string t = nuevaTemporal();
        emitir({TipoInstrIR::OP_BIN, t, izq, sym, der, "", op->linea});
        return t;
    }

    // Condicion usada como expresion booleana
    return generarCondicion(nodo);
}

// -----------------------------------------------------------------------
// Condiciones: retorna el temporal con el resultado booleano
// -----------------------------------------------------------------------
std::string GeneradorIR::generarCondicion(const Nodo& nodo) {

    if (auto* comp = dynamic_cast<const NodoComparacion*>(&nodo)) {
        std::string izq = generarExpresion(*comp->izquierda);
        std::string der = generarExpresion(*comp->derecha);
        std::string sym;
        if      (comp->comparador == "es igual a")          sym = "==";
        else if (comp->comparador == "es mayor que")         sym = ">";
        else if (comp->comparador == "es menor que")         sym = "<";
        else if (comp->comparador == "es mayor o igual que") sym = ">=";
        else if (comp->comparador == "es menor o igual que") sym = "<=";
        else                                                  sym = "?";
        std::string t = nuevaTemporal();
        emitir({TipoInstrIR::OP_BIN, t, izq, sym, der, "", comp->linea});
        return t;
    }

    if (auto* oplog = dynamic_cast<const NodoOpLogica*>(&nodo)) {
        std::string izq = generarCondicion(*oplog->izquierda);
        std::string der = generarCondicion(*oplog->derecha);
        std::string sym = (oplog->operador == "y") ? "&&" : "||";
        std::string t   = nuevaTemporal();
        emitir({TipoInstrIR::OP_BIN, t, izq, sym, der});
        return t;
    }

    if (auto* neg = dynamic_cast<const NodoNegar*>(&nodo)) {
        std::string src = generarCondicion(*neg->operando);
        std::string t   = nuevaTemporal();
        emitir({TipoInstrIR::NEGACION_LOGICA, t, src});
        return t;
    }

    return "_err";
}

// -----------------------------------------------------------------------
// Impresion del codigo intermedio (TAC)
// -----------------------------------------------------------------------
void GeneradorIR::imprimir(const std::vector<InstrIR>& codigo) {
    const std::string RST  = "\033[0m";
    const std::string BOLD = "\033[1m";
    const std::string DIM  = "\033[2m";
    const std::string CYN  = "\033[36m";
    const std::string YEL  = "\033[33m";
    const std::string GRN  = "\033[32m";
    const std::string MAG  = "\033[35m";

    int n = 0;
    for (const auto& ins : codigo) {
        switch (ins.tipo) {
            case TipoInstrIR::ETIQUETA:
                std::cout << "\n" << MAG << BOLD << ins.etiqueta << ":" << RST << "\n";
                break;
            case TipoInstrIR::ASIGNAR:
                std::cout << "  " << DIM << std::setw(3) << n++ << RST
                          << "  " << CYN << std::left << std::setw(12) << ins.resultado << RST
                          << " = " << GRN << ins.arg1 << RST << "\n";
                break;
            case TipoInstrIR::OP_BIN:
                std::cout << "  " << DIM << std::setw(3) << n++ << RST
                          << "  " << CYN << std::left << std::setw(12) << ins.resultado << RST
                          << " = " << GRN << ins.arg1 << RST
                          << " " << YEL << ins.operador << RST
                          << " " << GRN << ins.arg2 << RST << "\n";
                break;
            case TipoInstrIR::NEGACION_LOGICA:
                std::cout << "  " << DIM << std::setw(3) << n++ << RST
                          << "  " << CYN << std::left << std::setw(12) << ins.resultado << RST
                          << " = " << YEL << "!" << RST
                          << GRN << ins.arg1 << RST << "\n";
                break;
            case TipoInstrIR::SALTO:
                std::cout << "  " << DIM << std::setw(3) << n++ << RST
                          << "  " << BOLD << "goto " << RST
                          << MAG << ins.etiqueta << RST << "\n";
                break;
            case TipoInstrIR::SALTO_SI_FALSO:
                std::cout << "  " << DIM << std::setw(3) << n++ << RST
                          << "  " << BOLD << "si no " << RST
                          << GRN << ins.arg1 << RST
                          << BOLD << " goto " << RST
                          << MAG << ins.etiqueta << RST << "\n";
                break;
            case TipoInstrIR::MOSTRAR:
                std::cout << "  " << DIM << std::setw(3) << n++ << RST
                          << "  " << BOLD << "mostrar " << RST
                          << GRN << ins.arg1 << RST << "\n";
                break;
        }
    }
}
