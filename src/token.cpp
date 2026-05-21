#include "token.hpp"

Token::Token(TipoToken tipo, std::string valor, int linea, int columna)
    : tipo(tipo), valor(std::move(valor)), linea(linea), columna(columna) {}

std::string Token::nombreTipo() const {
    switch (tipo) {
        case TipoToken::DEFINIR:       return "DEFINIR";
        case TipoToken::COMO:          return "COMO";
        case TipoToken::SI:            return "SI";
        case TipoToken::ENTONCES:      return "ENTONCES";
        case TipoToken::SINO:          return "SINO";
        case TipoToken::FIN:           return "FIN";
        case TipoToken::REPETIR:       return "REPETIR";
        case TipoToken::VECES:         return "VECES";
        case TipoToken::MIENTRAS:      return "MIENTRAS";
        case TipoToken::MOSTRAR:       return "MOSTRAR";
        case TipoToken::MAS:           return "MAS";
        case TipoToken::MENOS:         return "MENOS";
        case TipoToken::POR:           return "POR";
        case TipoToken::ENTRE:         return "ENTRE";
        case TipoToken::ES:            return "ES";
        case TipoToken::MAYOR:         return "MAYOR";
        case TipoToken::MENOR:         return "MENOR";
        case TipoToken::IGUAL:         return "IGUAL";
        case TipoToken::QUE:           return "QUE";
        case TipoToken::A:             return "A";
        case TipoToken::Y:             return "Y";
        case TipoToken::O:             return "O";
        case TipoToken::NO:            return "NO";
        case TipoToken::NUMERO:        return "NUMERO";
        case TipoToken::TEXTO:         return "TEXTO";
        case TipoToken::VERDADERO:     return "VERDADERO";
        case TipoToken::FALSO:         return "FALSO";
        case TipoToken::IDENTIFICADOR: return "IDENTIFICADOR";
        case TipoToken::PAREN_IZQ:     return "PAREN_IZQ";
        case TipoToken::PAREN_DER:     return "PAREN_DER";
        case TipoToken::NUEVA_LINEA:   return "NUEVA_LINEA";
        case TipoToken::FIN_ARCHIVO:   return "FIN_ARCHIVO";
        case TipoToken::ERROR:         return "ERROR";
        default:                       return "DESCONOCIDO";
    }
}

// Devuelve la categoria visual: keyword | operador | literal | identificador | control | error
std::string Token::categoriaColor() const {
    switch (tipo) {
        case TipoToken::DEFINIR: case TipoToken::COMO:
        case TipoToken::SI:      case TipoToken::ENTONCES:
        case TipoToken::SINO:    case TipoToken::FIN:
        case TipoToken::REPETIR: case TipoToken::VECES:
        case TipoToken::MIENTRAS:case TipoToken::MOSTRAR:
            return "keyword";
        case TipoToken::MAS:   case TipoToken::MENOS:
        case TipoToken::POR:   case TipoToken::ENTRE:
        case TipoToken::ES:    case TipoToken::MAYOR:
        case TipoToken::MENOR: case TipoToken::IGUAL:
        case TipoToken::QUE:   case TipoToken::A:
        case TipoToken::Y:     case TipoToken::O:
        case TipoToken::NO:
            return "operador";
        case TipoToken::NUMERO:    case TipoToken::TEXTO:
        case TipoToken::VERDADERO: case TipoToken::FALSO:
            return "literal";
        case TipoToken::IDENTIFICADOR:
            return "identificador";
        case TipoToken::PAREN_IZQ: case TipoToken::PAREN_DER:
        case TipoToken::NUEVA_LINEA: case TipoToken::FIN_ARCHIVO:
            return "control";
        case TipoToken::ERROR:
            return "error";
        default:
            return "control";
    }
}
