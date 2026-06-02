#pragma once
#include "token.hpp"
#include <string>
#include <vector>
#include <unordered_map>

class Lexer {
public:
    explicit Lexer(const std::string& fuente);

    std::vector<Token>              tokenizar();
    bool                            tieneErrores() const;
    const std::vector<std::string>& errores()      const;

private:
    std::string              fuente_;
    size_t                   pos_;
    int                      linea_;
    int                      columna_;
    std::vector<std::string> errores_;

    // Tabla de palabras clave — agregar nuevas palabras aqui
    static const std::unordered_map<std::string, TipoToken> PALABRAS_CLAVE;

    char actual()    const;
    char siguiente() const;
    void avanzar();
    void saltarEspaciosYTabs();

    Token leerPalabra();
    Token leerNumero();
    Token leerTexto();
    void  registrarError(const std::string& msg);

    static std::string aMinusculas(const std::string& s);
};
