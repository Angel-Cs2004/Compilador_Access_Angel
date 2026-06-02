#include "parser.hpp"
#include <stdexcept>

// -----------------------------------------------------------------------
// Constructor
// -----------------------------------------------------------------------
Parser::Parser(std::vector<Token> tokens)
    : tokens_(std::move(tokens)), pos_(0) {}

// -----------------------------------------------------------------------
// Navegacion
// -----------------------------------------------------------------------
const Token& Parser::actual() const {
    return tokens_[pos_];
}

const Token& Parser::ver(int offset) const {
    size_t idx = pos_ + static_cast<size_t>(offset);
    if (idx >= tokens_.size()) return tokens_.back(); // FIN_ARCHIVO
    return tokens_[idx];
}

void Parser::avanzar() {
    if (!esFin()) pos_++;
}

bool Parser::esActual(TipoToken t) const {
    return actual().tipo == t;
}

bool Parser::esFin() const {
    return actual().tipo == TipoToken::FIN_ARCHIVO;
}

Token Parser::consumir(TipoToken tipo, const std::string& esperado) {
    if (actual().tipo == tipo) {
        Token t = actual();
        avanzar();
        return t;
    }
    registrarError("Se esperaba '" + esperado + "', se encontro '" + actual().valor + "'");
    // Devuelve un token de error sin avanzar para que el llamador decida
    return Token(TipoToken::ERROR, esperado, actual().linea, actual().columna);
}

void Parser::saltarNuevasLineas() {
    while (esActual(TipoToken::NUEVA_LINEA)) avanzar();
}

void Parser::saltarHastaFinLinea() {
    while (!esFin() && !esActual(TipoToken::NUEVA_LINEA)) avanzar();
    if (esActual(TipoToken::NUEVA_LINEA)) avanzar();
}

void Parser::registrarError(const std::string& msg) {
    errores_.push_back(
        "[Linea " + std::to_string(actual().linea) +
        ", Col "  + std::to_string(actual().columna) + "] " + msg
    );
}

// -----------------------------------------------------------------------
// Punto de entrada
// -----------------------------------------------------------------------
std::unique_ptr<NodoPrograma> Parser::parsear() {
    auto programa = std::make_unique<NodoPrograma>();
    saltarNuevasLineas();

    while (!esFin()) {
        auto instr = parsearInstruccion();
        if (instr) programa->instrucciones.push_back(std::move(instr));
        saltarNuevasLineas();
    }
    return programa;
}

// -----------------------------------------------------------------------
// Bloque de instrucciones (hasta "fin", "sino" o FIN_ARCHIVO)
// -----------------------------------------------------------------------
std::vector<NodoPtr> Parser::parsearBloque() {
    std::vector<NodoPtr> bloque;
    saltarNuevasLineas();

    while (!esFin()
           && !esActual(TipoToken::FIN)
           && !esActual(TipoToken::SINO)) {
        auto instr = parsearInstruccion();
        if (instr) bloque.push_back(std::move(instr));
        saltarNuevasLineas();
    }
    return bloque;
}

// -----------------------------------------------------------------------
// Despachador de instrucciones
// -----------------------------------------------------------------------
NodoPtr Parser::parsearInstruccion() {
    saltarNuevasLineas();
    if (esFin()) return nullptr;

    switch (actual().tipo) {
        case TipoToken::DEFINIR:  return parsearDeclaracion();
        case TipoToken::SI:       return parsearCondicional();
        case TipoToken::REPETIR:  return parsearBucleRepetir();
        case TipoToken::MIENTRAS: return parsearBucleMientras();
        case TipoToken::MOSTRAR:  return parsearMostrar();
        default:
            registrarError("Instruccion no reconocida: '" + actual().valor + "'");
            saltarHastaFinLinea();
            return nullptr;
    }
}

// -----------------------------------------------------------------------
// definir IDENTIFICADOR como expresion
// -----------------------------------------------------------------------
std::unique_ptr<NodoDeclaracion> Parser::parsearDeclaracion() {
    consumir(TipoToken::DEFINIR, "definir");
    Token nombre = consumir(TipoToken::IDENTIFICADOR, "nombre de variable");
    consumir(TipoToken::COMO, "como");
    auto expr = parsearExpresion();
    auto nodo = std::make_unique<NodoDeclaracion>(nombre.valor, std::move(expr));
    nodo->linea   = nombre.linea;
    nodo->columna = nombre.columna;
    return nodo;
}

// -----------------------------------------------------------------------
// si condicion entonces
//     bloque
// [sino
//     bloque]
// fin si
// -----------------------------------------------------------------------
std::unique_ptr<NodoCondicional> Parser::parsearCondicional() {
    consumir(TipoToken::SI, "si");
    auto cond = parsearCondicion();
    consumir(TipoToken::ENTONCES, "entonces");
    saltarNuevasLineas();

    auto nodo = std::make_unique<NodoCondicional>();
    nodo->condicion = std::move(cond);
    nodo->entonces  = parsearBloque();

    if (esActual(TipoToken::SINO)) {
        avanzar(); // consume "sino"
        saltarNuevasLineas();
        nodo->sino = parsearBloque();
    }

    consumir(TipoToken::FIN, "fin");
    consumir(TipoToken::SI, "si");
    return nodo;
}

// -----------------------------------------------------------------------
// repetir expresion veces
//     bloque
// fin repetir
// -----------------------------------------------------------------------
std::unique_ptr<NodoBucleRepetir> Parser::parsearBucleRepetir() {
    Token tok = actual();
    consumir(TipoToken::REPETIR, "repetir");
    auto veces = parsearExpresion();
    consumir(TipoToken::VECES, "veces");
    saltarNuevasLineas();

    auto nodo = std::make_unique<NodoBucleRepetir>();
    nodo->linea   = tok.linea;
    nodo->columna = tok.columna;
    nodo->veces  = std::move(veces);
    nodo->cuerpo = parsearBloque();

    consumir(TipoToken::FIN, "fin");
    consumir(TipoToken::REPETIR, "repetir");
    return nodo;
}

// -----------------------------------------------------------------------
// mientras condicion
//     bloque
// fin mientras
// -----------------------------------------------------------------------
std::unique_ptr<NodoBucleMientras> Parser::parsearBucleMientras() {
    consumir(TipoToken::MIENTRAS, "mientras");
    auto cond = parsearCondicion();
    saltarNuevasLineas();

    auto nodo = std::make_unique<NodoBucleMientras>();
    nodo->condicion = std::move(cond);
    nodo->cuerpo    = parsearBloque();

    consumir(TipoToken::FIN, "fin");
    consumir(TipoToken::MIENTRAS, "mientras");
    return nodo;
}

// -----------------------------------------------------------------------
// mostrar expresion
// -----------------------------------------------------------------------
std::unique_ptr<NodoMostrar> Parser::parsearMostrar() {
    consumir(TipoToken::MOSTRAR, "mostrar");
    auto expr = parsearExpresion();
    return std::make_unique<NodoMostrar>(std::move(expr));
}

// -----------------------------------------------------------------------
// Expresion aritmetica — precedencia ascendente
//
// expresion → termino (("mas" | "menos") termino)*
// termino   → factor  (("por" | "entre") factor)*
// factor    → NUMERO | TEXTO | BOOL | IDENT | "(" expresion ")"
// -----------------------------------------------------------------------
NodoPtr Parser::parsearExpresion() {
    auto izq = parsearTermino();

    while (esActual(TipoToken::MAS) || esActual(TipoToken::MENOS)) {
        std::string op  = actual().valor;
        int lin = actual().linea, col = actual().columna;
        avanzar();
        auto der = parsearTermino();
        auto res = std::make_unique<NodoOpBinaria>(std::move(izq), op, std::move(der));
        res->linea = lin; res->columna = col;
        izq = std::move(res);
    }
    return izq;
}

NodoPtr Parser::parsearTermino() {
    auto izq = parsearFactor();

    while (esActual(TipoToken::POR) || esActual(TipoToken::ENTRE)) {
        std::string op  = actual().valor;
        int lin = actual().linea, col = actual().columna;
        avanzar();
        auto der = parsearFactor();
        auto res = std::make_unique<NodoOpBinaria>(std::move(izq), op, std::move(der));
        res->linea = lin; res->columna = col;
        izq = std::move(res);
    }
    return izq;
}

NodoPtr Parser::parsearFactor() {
    // Numero
    if (esActual(TipoToken::NUMERO)) {
        double val = std::stod(actual().valor);
        avanzar();
        return std::make_unique<NodoNumero>(val);
    }
    // Texto
    if (esActual(TipoToken::TEXTO)) {
        std::string val = actual().valor;
        avanzar();
        return std::make_unique<NodoTexto>(val);
    }
    // Booleanos
    if (esActual(TipoToken::VERDADERO)) { avanzar(); return std::make_unique<NodoBooleano>(true);  }
    if (esActual(TipoToken::FALSO))     { avanzar(); return std::make_unique<NodoBooleano>(false); }
    // Identificador
    if (esActual(TipoToken::IDENTIFICADOR)) {
        std::string nombre = actual().valor;
        int lin = actual().linea, col = actual().columna;
        avanzar();
        auto nodo = std::make_unique<NodoIdentificador>(nombre);
        nodo->linea = lin; nodo->columna = col;
        return nodo;
    }
    // Expresion entre parentesis
    if (esActual(TipoToken::PAREN_IZQ)) {
        avanzar();
        auto expr = parsearExpresion();
        consumir(TipoToken::PAREN_DER, ")");
        return expr;
    }

    // Error de recuperacion: se esperaba un valor
    registrarError("Se esperaba un valor o expresion, se encontro '" + actual().valor + "'");
    avanzar();
    return std::make_unique<NodoNumero>(0);
}

// -----------------------------------------------------------------------
// Condicion
//
// condicion       → condicion_base (("y" | "o") condicion_base)*
//                 | "no" condicion_base
// condicion_base  → expresion comparador expresion
//
// Comparadores soportados:
//   "es igual a"
//   "es mayor que"
//   "es menor que"
//   "es mayor o igual que"
//   "es menor o igual que"
// -----------------------------------------------------------------------
NodoPtr Parser::parsearCondicion() {
    // Negacion
    if (esActual(TipoToken::NO)) {
        avanzar();
        auto operando = parsearCondicionBase();
        return std::make_unique<NodoNegar>(std::move(operando));
    }

    auto izq = parsearCondicionBase();

    // Encadenamiento con "y" / "o"
    while (esActual(TipoToken::Y) || esActual(TipoToken::O)) {
        std::string op = actual().valor;
        avanzar();
        auto der = parsearCondicionBase();
        izq = std::make_unique<NodoOpLogica>(std::move(izq), op, std::move(der));
    }
    return izq;
}

NodoPtr Parser::parsearCondicionBase() {
    int lin = actual().linea, col = actual().columna;
    auto izq  = parsearExpresion();
    auto comp = parsearComparador();
    auto der  = parsearExpresion();
    auto nodo = std::make_unique<NodoComparacion>(std::move(izq), comp, std::move(der));
    nodo->linea = lin; nodo->columna = col;
    return nodo;
}

// Consume los tokens del comparador y devuelve su forma canonica
std::string Parser::parsearComparador() {
    if (!esActual(TipoToken::ES)) {
        registrarError("Se esperaba un comparador ('es ...'), se encontro '" + actual().valor + "'");
        return "desconocido";
    }
    avanzar(); // consume "es"

    // "es igual a"
    if (esActual(TipoToken::IGUAL)) {
        avanzar();
        consumir(TipoToken::A, "a");
        return "es igual a";
    }
    // "es mayor [o igual] que"
    if (esActual(TipoToken::MAYOR)) {
        avanzar();
        if (esActual(TipoToken::O)) {
            avanzar();
            consumir(TipoToken::IGUAL, "igual");
            consumir(TipoToken::QUE,   "que");
            return "es mayor o igual que";
        }
        consumir(TipoToken::QUE, "que");
        return "es mayor que";
    }
    // "es menor [o igual] que"
    if (esActual(TipoToken::MENOR)) {
        avanzar();
        if (esActual(TipoToken::O)) {
            avanzar();
            consumir(TipoToken::IGUAL, "igual");
            consumir(TipoToken::QUE,   "que");
            return "es menor o igual que";
        }
        consumir(TipoToken::QUE, "que");
        return "es menor que";
    }

    registrarError("Comparador desconocido despues de 'es': '" + actual().valor + "'");
    return "desconocido";
}

// -----------------------------------------------------------------------
// Accesores publicos
// -----------------------------------------------------------------------
bool Parser::tieneErrores() const { return !errores_.empty(); }

const std::vector<std::string>& Parser::errores() const { return errores_; }
