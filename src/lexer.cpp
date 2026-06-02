#include "lexer.hpp"
#include <cctype>
#include <algorithm>

// -----------------------------------------------------------------------
// Para agregar una nueva palabra clave al lenguaje, solo añade una entrada
// aqui. El resto del lexer no necesita cambios.
// -----------------------------------------------------------------------
const std::unordered_map<std::string, TipoToken> Lexer::PALABRAS_CLAVE = {
    // Declaracion
    {"definir",   TipoToken::DEFINIR},
    {"como",      TipoToken::COMO},
    // Condicional
    {"si",        TipoToken::SI},
    {"entonces",  TipoToken::ENTONCES},
    {"sino",      TipoToken::SINO},
    {"fin",       TipoToken::FIN},
    // Bucles
    {"repetir",   TipoToken::REPETIR},
    {"veces",     TipoToken::VECES},
    {"mientras",  TipoToken::MIENTRAS},
    // Salida
    {"mostrar",   TipoToken::MOSTRAR},
    // Aritmetica
    {"mas",       TipoToken::MAS},
    {"menos",     TipoToken::MENOS},
    {"por",       TipoToken::POR},
    {"entre",     TipoToken::ENTRE},
    // Comparadores
    {"es",        TipoToken::ES},
    {"mayor",     TipoToken::MAYOR},
    {"menor",     TipoToken::MENOR},
    {"igual",     TipoToken::IGUAL},
    {"que",       TipoToken::QUE},
    {"a",         TipoToken::A},
    // Logicos
    {"y",         TipoToken::Y},
    {"o",         TipoToken::O},
    {"no",        TipoToken::NO},
    // Literales booleanos
    {"verdadero", TipoToken::VERDADERO},
    {"falso",     TipoToken::FALSO},
};

// -----------------------------------------------------------------------
// Constructor
// -----------------------------------------------------------------------
Lexer::Lexer(const std::string& fuente)
    : fuente_(fuente), pos_(0), linea_(1), columna_(1) {}

// -----------------------------------------------------------------------
// Navegacion sobre la fuente
// -----------------------------------------------------------------------
char Lexer::actual() const {
    return pos_ < fuente_.size() ? fuente_[pos_] : '\0';
}

char Lexer::siguiente() const {
    return (pos_ + 1) < fuente_.size() ? fuente_[pos_ + 1] : '\0';
}

void Lexer::avanzar() {
    if (pos_ >= fuente_.size()) return;
    if (fuente_[pos_] == '\n') {
        linea_++;
        columna_ = 1;
    } else {
        columna_++;
    }
    pos_++;
}

void Lexer::saltarEspaciosYTabs() {
    while (actual() == ' ' || actual() == '\t' || actual() == '\r')
        avanzar();
}

// -----------------------------------------------------------------------
// Utilidades
// -----------------------------------------------------------------------
std::string Lexer::aMinusculas(const std::string& s) {
    std::string resultado = s;
    std::transform(resultado.begin(), resultado.end(), resultado.begin(),
                   [](unsigned char c) { return std::tolower(c); });
    return resultado;
}

void Lexer::registrarError(const std::string& msg) {
    errores_.push_back(
        "[Linea " + std::to_string(linea_) +
        ", Col "  + std::to_string(columna_) + "] " + msg
    );
}

// -----------------------------------------------------------------------
// Lectores especificos
// -----------------------------------------------------------------------
Token Lexer::leerPalabra() {
    int col_inicio = columna_;
    std::string palabra;

    // Primer caracter: letra o guion bajo
    while (std::isalpha(static_cast<unsigned char>(actual()))
           || actual() == '_'
           // digitos permitidos despues del primero
           || (!palabra.empty() && std::isdigit(static_cast<unsigned char>(actual())))) {
        palabra += actual();
        avanzar();
    }

    // Busqueda case-insensitive en tabla de palabras clave
    auto it = PALABRAS_CLAVE.find(aMinusculas(palabra));
    if (it != PALABRAS_CLAVE.end())
        return Token(it->second, palabra, linea_, col_inicio);

    return Token(TipoToken::IDENTIFICADOR, palabra, linea_, col_inicio);
}

Token Lexer::leerNumero() {
    int col_inicio = columna_;
    std::string num;
    bool decimal = false;

    while (std::isdigit(static_cast<unsigned char>(actual()))
           || (actual() == '.' && !decimal && std::isdigit(static_cast<unsigned char>(siguiente())))) {
        if (actual() == '.') decimal = true;
        num += actual();
        avanzar();
    }
    return Token(TipoToken::NUMERO, num, linea_, col_inicio);
}

Token Lexer::leerTexto() {
    int col_inicio = columna_;
    avanzar(); // consume la comilla de apertura "
    std::string contenido;

    while (actual() != '"' && actual() != '\0' && actual() != '\n') {
        // secuencia de escape basica \n \t
        if (actual() == '\\' && (siguiente() == 'n' || siguiente() == 't')) {
            contenido += (siguiente() == 'n') ? '\n' : '\t';
            avanzar(); avanzar();
        } else {
            contenido += actual();
            avanzar();
        }
    }

    if (actual() == '"') {
        avanzar(); // consume la comilla de cierre
    } else {
        registrarError("Cadena de texto sin cerrar (falta comilla de cierre \")");
    }

    return Token(TipoToken::TEXTO, contenido, linea_, col_inicio);
}

// -----------------------------------------------------------------------
// Punto de entrada principal
// -----------------------------------------------------------------------
std::vector<Token> Lexer::tokenizar() {
    std::vector<Token> tokens;
    tokens.reserve(64);

    while (pos_ < fuente_.size()) {
        saltarEspaciosYTabs();

        if (actual() == '\0') break;

        // Comentario de linea: # hasta fin de linea
        if (actual() == '#') {
            while (actual() != '\n' && actual() != '\0')
                avanzar();
            continue;
        }

        // Nueva linea — es un token significativo para el parser
        if (actual() == '\n') {
            tokens.emplace_back(TipoToken::NUEVA_LINEA, "\\n", linea_, columna_);
            avanzar();
            continue;
        }

        // Parentesis
        if (actual() == '(') {
            tokens.emplace_back(TipoToken::PAREN_IZQ, "(", linea_, columna_);
            avanzar();
            continue;
        }
        if (actual() == ')') {
            tokens.emplace_back(TipoToken::PAREN_DER, ")", linea_, columna_);
            avanzar();
            continue;
        }

        // Numero
        if (std::isdigit(static_cast<unsigned char>(actual()))) {
            tokens.push_back(leerNumero());
            continue;
        }

        // Cadena de texto
        if (actual() == '"') {
            tokens.push_back(leerTexto());
            continue;
        }

        // Palabra clave o identificador
        if (std::isalpha(static_cast<unsigned char>(actual())) || actual() == '_') {
            tokens.push_back(leerPalabra());
            continue;
        }

        // Caracter no reconocido
        registrarError("Caracter desconocido '" + std::string(1, actual()) + "'");
        avanzar();
    }

    tokens.emplace_back(TipoToken::FIN_ARCHIVO, "EOF", linea_, columna_);
    return tokens;
}

bool Lexer::tieneErrores() const { return !errores_.empty(); }

const std::vector<std::string>& Lexer::errores() const { return errores_; }
