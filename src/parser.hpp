#pragma once
#include "token.hpp"
#include "ast.hpp"
#include <vector>
#include <string>
#include <memory>

class Parser {
public:
    explicit Parser(std::vector<Token> tokens);

    std::unique_ptr<NodoPrograma>   parsear();
    bool                            tieneErrores() const;
    const std::vector<std::string>& errores()      const;

private:
    std::vector<Token>       tokens_;
    size_t                   pos_;
    std::vector<std::string> errores_;

    // --- Navegacion ---
    const Token& actual()    const;
    const Token& ver(int offset) const; // lookahead sin avanzar
    Token        consumir(TipoToken tipo, const std::string& esperado);
    void         avanzar();
    bool         esActual(TipoToken t) const;
    bool         esFin()    const;

    // Salta NUEVA_LINEA consecutivos
    void saltarNuevasLineas();
    // Avanza hasta el proximo NUEVA_LINEA (recuperacion de errores)
    void saltarHastaFinLinea();
    // Registra un error con posicion
    void registrarError(const std::string& msg);

    // --- Reglas gramaticales ---
    NodoPtr              parsearInstruccion();
    std::vector<NodoPtr> parsearBloque();   // instrucciones hasta "fin" o "sino"

    std::unique_ptr<NodoDeclaracion>   parsearDeclaracion();
    std::unique_ptr<NodoCondicional>   parsearCondicional();
    std::unique_ptr<NodoBucleRepetir>  parsearBucleRepetir();
    std::unique_ptr<NodoBucleMientras> parsearBucleMientras();
    std::unique_ptr<NodoMostrar>       parsearMostrar();

    // Expresiones aritmeticas (precedencia: expresion > termino > factor)
    NodoPtr parsearExpresion();
    NodoPtr parsearTermino();
    NodoPtr parsearFactor();

    // Condiciones
    NodoPtr     parsearCondicion();
    NodoPtr     parsearCondicionBase();
    std::string parsearComparador();
};
