#include "semantico.hpp"

// -----------------------------------------------------------------------
// Utilidades
// -----------------------------------------------------------------------
std::string nombreTipo(TipoValor t) {
    switch (t) {
        case TipoValor::NUMERO:      return "numero";
        case TipoValor::TEXTO:       return "texto";
        case TipoValor::BOOLEANO:    return "booleano";
        case TipoValor::DESCONOCIDO: return "desconocido";
    }
    return "desconocido";
}

static std::string ubicacion(int linea, int columna) {
    if (linea < 0) return "";
    return "[Linea " + std::to_string(linea) + ", Col " + std::to_string(columna) + "] ";
}

void AnalizadorSemantico::registrarError(const std::string& msg, int l, int c) {
    errores_.push_back(ubicacion(l, c) + msg);
}

void AnalizadorSemantico::registrarAdvertencia(const std::string& msg, int l, int c) {
    advertencias_.push_back(ubicacion(l, c) + msg);
}

// -----------------------------------------------------------------------
// Punto de entrada
// -----------------------------------------------------------------------
void AnalizadorSemantico::analizar(const NodoPrograma& programa) {
    tabla_.clear();
    errores_.clear();
    advertencias_.clear();
    analizarBloque(programa.instrucciones);
}

void AnalizadorSemantico::analizarBloque(const std::vector<NodoPtr>& bloque) {
    for (const auto& n : bloque)
        if (n) analizarInstruccion(*n);
}

// -----------------------------------------------------------------------
// Instrucciones
// -----------------------------------------------------------------------
void AnalizadorSemantico::analizarInstruccion(const Nodo& nodo) {

    // definir IDENT como EXPR
    if (auto* decl = dynamic_cast<const NodoDeclaracion*>(&nodo)) {
        TipoValor t = analizarExpresion(*decl->expresion);
        auto it = tabla_.find(decl->nombre);
        if (it != tabla_.end()) {
            // Redeclaracion: advertencia, se actualiza el tipo
            registrarAdvertencia(
                "La variable '" + decl->nombre + "' ya estaba declarada "
                "(tipo anterior: " + nombreTipo(it->second.tipo) +
                ", tipo nuevo: "   + nombreTipo(t) + ")",
                decl->linea, decl->columna
            );
            it->second = {t, decl->linea, decl->columna};
        } else {
            tabla_[decl->nombre] = {t, decl->linea, decl->columna};
        }
        return;
    }

    // mostrar EXPR  — acepta cualquier tipo
    if (auto* most = dynamic_cast<const NodoMostrar*>(&nodo)) {
        analizarExpresion(*most->expresion);
        return;
    }

    // si COND entonces BLOQUE [sino BLOQUE] fin si
    if (auto* cond = dynamic_cast<const NodoCondicional*>(&nodo)) {
        analizarCondicion(*cond->condicion);
        analizarBloque(cond->entonces);
        analizarBloque(cond->sino);
        return;
    }

    // repetir EXPR veces BLOQUE fin repetir
    if (auto* rep = dynamic_cast<const NodoBucleRepetir*>(&nodo)) {
        TipoValor t = analizarExpresion(*rep->veces);
        if (t != TipoValor::NUMERO && t != TipoValor::DESCONOCIDO) {
            registrarError(
                "La cantidad de repeticiones debe ser un numero, "
                "pero se obtuvo '" + nombreTipo(t) + "'",
                rep->linea, rep->columna
            );
        }
        analizarBloque(rep->cuerpo);
        return;
    }

    // mientras COND BLOQUE fin mientras
    if (auto* mien = dynamic_cast<const NodoBucleMientras*>(&nodo)) {
        analizarCondicion(*mien->condicion);
        analizarBloque(mien->cuerpo);
        return;
    }
}

// -----------------------------------------------------------------------
// Expresiones: retorna el tipo inferido
// -----------------------------------------------------------------------
TipoValor AnalizadorSemantico::analizarExpresion(const Nodo& nodo) {

    // Literales — tipo conocido directamente
    if (dynamic_cast<const NodoNumero*>(&nodo))   return TipoValor::NUMERO;
    if (dynamic_cast<const NodoTexto*>(&nodo))    return TipoValor::TEXTO;
    if (dynamic_cast<const NodoBooleano*>(&nodo)) return TipoValor::BOOLEANO;

    // Identificador: buscar en tabla de simbolos
    if (auto* id = dynamic_cast<const NodoIdentificador*>(&nodo)) {
        auto it = tabla_.find(id->nombre);
        if (it == tabla_.end()) {
            registrarError(
                "Variable '" + id->nombre + "' usada antes de ser declarada",
                id->linea, id->columna
            );
            return TipoValor::DESCONOCIDO;  // evita errores en cascada
        }
        return it->second.tipo;
    }

    // Operacion aritmetica: mas, menos, por, entre
    if (auto* op = dynamic_cast<const NodoOpBinaria*>(&nodo)) {
        TipoValor izq = analizarExpresion(*op->izquierda);
        TipoValor der = analizarExpresion(*op->derecha);

        // Caso especial: 'mas' permite concatenar dos textos
        if (op->operador == "mas"
            && izq == TipoValor::TEXTO
            && der == TipoValor::TEXTO)
            return TipoValor::TEXTO;

        // Para el resto de operaciones ambos lados deben ser numero
        if (izq != TipoValor::NUMERO && izq != TipoValor::DESCONOCIDO)
            registrarError(
                "Operacion '" + op->operador + "' requiere numeros; "
                "el operando izquierdo es de tipo '" + nombreTipo(izq) + "'",
                op->linea, op->columna
            );
        if (der != TipoValor::NUMERO && der != TipoValor::DESCONOCIDO)
            registrarError(
                "Operacion '" + op->operador + "' requiere numeros; "
                "el operando derecho es de tipo '" + nombreTipo(der) + "'",
                op->linea, op->columna
            );
        return TipoValor::NUMERO;
    }

    // Si por alguna razon aparece un nodo de condicion en contexto de expresion
    if (dynamic_cast<const NodoComparacion*>(&nodo) ||
        dynamic_cast<const NodoOpLogica*>(&nodo)    ||
        dynamic_cast<const NodoNegar*>(&nodo)) {
        analizarCondicion(nodo);
        return TipoValor::BOOLEANO;
    }

    return TipoValor::DESCONOCIDO;
}

// -----------------------------------------------------------------------
// Condiciones: verifica coherencia logica
// -----------------------------------------------------------------------
void AnalizadorSemantico::analizarCondicion(const Nodo& nodo) {

    // comparacion: izq COMPARADOR der
    if (auto* comp = dynamic_cast<const NodoComparacion*>(&nodo)) {
        TipoValor izq = analizarExpresion(*comp->izquierda);
        TipoValor der = analizarExpresion(*comp->derecha);
        // Solo reportar si ambos tipos son conocidos y distintos
        if (izq != TipoValor::DESCONOCIDO
            && der != TipoValor::DESCONOCIDO
            && izq != der) {
            registrarError(
                "Comparacion de tipos incompatibles: '"
                + nombreTipo(izq) + "' " + comp->comparador
                + " '" + nombreTipo(der) + "'",
                comp->linea, comp->columna
            );
        }
        return;
    }

    // condicion_base Y/O condicion_base
    if (auto* oplog = dynamic_cast<const NodoOpLogica*>(&nodo)) {
        analizarCondicion(*oplog->izquierda);
        analizarCondicion(*oplog->derecha);
        return;
    }

    // NO condicion
    if (auto* neg = dynamic_cast<const NodoNegar*>(&nodo)) {
        analizarCondicion(*neg->operando);
        return;
    }
}

// -----------------------------------------------------------------------
// Accesores
// -----------------------------------------------------------------------
bool AnalizadorSemantico::tieneErrores()      const { return !errores_.empty();      }
bool AnalizadorSemantico::tieneAdvertencias() const { return !advertencias_.empty(); }

const std::vector<std::string>& AnalizadorSemantico::errores()      const { return errores_;      }
const std::vector<std::string>& AnalizadorSemantico::advertencias() const { return advertencias_; }
