#include "ast.hpp"
#include <iostream>
#include <iomanip>
#include <sstream>

// -----------------------------------------------------------------------
// Colores y simbolos del arbol
// -----------------------------------------------------------------------
namespace {
    const std::string RST    = "\033[0m";
    const std::string BOLD   = "\033[1m";
    const std::string DIM    = "\033[2m";
    const std::string CYN    = "\033[36m";  // instrucciones
    const std::string GRN    = "\033[32m";  // literales
    const std::string YEL    = "\033[33m";  // operadores
    const std::string BLU    = "\033[34m";  // palabras clave / estructuras
    const std::string MAG    = "\033[35m";  // condiciones
    const std::string WHT    = "\033[37m";  // identificadores

    const std::string RAMA   = "├── "; // ├──
    const std::string ULTIMO = "└── "; // └──
    const std::string VERT   = "│   ";            // │
    const std::string ESP    = "    ";

    // Imprime la linea del nodo con el conector correcto
    void cabecera(const std::string& prefijo, bool esUltimo,
                  const std::string& color, const std::string& texto) {
        std::cout << DIM << prefijo << RST
                  << DIM << (esUltimo ? ULTIMO : RAMA) << RST
                  << color << BOLD << texto << RST << "\n";
    }

    // Calcula el prefijo para los hijos
    std::string hijoPrefijo(const std::string& prefijo, bool esUltimo) {
        return prefijo + (esUltimo ? ESP : VERT);
    }
}

// -----------------------------------------------------------------------
// Impresion de literales
// -----------------------------------------------------------------------
void NodoNumero::imprimir(const std::string& p, bool u) const {
    std::ostringstream ss;
    ss << std::fixed << std::setprecision(
        (valor == static_cast<int>(valor)) ? 0 : 6) << valor;
    cabecera(p, u, GRN, "Numero (" + ss.str() + ")");
}

void NodoTexto::imprimir(const std::string& p, bool u) const {
    cabecera(p, u, GRN, "Texto (\"" + valor + "\")");
}

void NodoBooleano::imprimir(const std::string& p, bool u) const {
    cabecera(p, u, GRN, std::string("Booleano (") + (valor ? "verdadero" : "falso") + ")");
}

void NodoIdentificador::imprimir(const std::string& p, bool u) const {
    cabecera(p, u, WHT, "Identificador (" + nombre + ")");
}

// -----------------------------------------------------------------------
// Impresion de expresiones aritmeticas
// -----------------------------------------------------------------------
void NodoOpBinaria::imprimir(const std::string& p, bool u) const {
    cabecera(p, u, YEL, "OpBinaria [" + operador + "]");
    std::string np = hijoPrefijo(p, u);
    izquierda->imprimir(np, false);
    derecha->imprimir(np, true);
}

// -----------------------------------------------------------------------
// Impresion de condiciones
// -----------------------------------------------------------------------
void NodoComparacion::imprimir(const std::string& p, bool u) const {
    cabecera(p, u, MAG, "Comparacion [" + comparador + "]");
    std::string np = hijoPrefijo(p, u);
    izquierda->imprimir(np, false);
    derecha->imprimir(np, true);
}

void NodoOpLogica::imprimir(const std::string& p, bool u) const {
    cabecera(p, u, MAG, "OpLogica [" + operador + "]");
    std::string np = hijoPrefijo(p, u);
    izquierda->imprimir(np, false);
    derecha->imprimir(np, true);
}

void NodoNegar::imprimir(const std::string& p, bool u) const {
    cabecera(p, u, MAG, "Negar");
    operando->imprimir(hijoPrefijo(p, u), true);
}

// -----------------------------------------------------------------------
// Impresion de instrucciones
// -----------------------------------------------------------------------
void NodoDeclaracion::imprimir(const std::string& p, bool u) const {
    cabecera(p, u, CYN, "Declaracion [" + nombre + "]");
    expresion->imprimir(hijoPrefijo(p, u), true);
}

void NodoCondicional::imprimir(const std::string& p, bool u) const {
    cabecera(p, u, BLU, "Condicional");
    std::string np = hijoPrefijo(p, u);

    bool tieneSino = !sino.empty();

    // Condicion (nunca es el ultimo hijo — siempre le sigue "Entonces")
    condicion->imprimir(np, false);

    // Bloque entonces: es ultimo solo si no hay sino
    std::string conEnton = tieneSino ? RAMA : ULTIMO;
    std::string prefEnton = tieneSino ? VERT  : ESP;
    std::cout << DIM << np << conEnton << RST << BLU << BOLD << "Entonces\n" << RST;
    std::string npEnt = np + prefEnton;
    for (size_t i = 0; i < entonces.size(); i++)
        entonces[i]->imprimir(npEnt, i == entonces.size() - 1);

    // Bloque sino (opcional)
    if (tieneSino) {
        std::cout << DIM << np << ULTIMO << RST << BLU << BOLD << "Sino\n" << RST;
        std::string npSino = np + ESP;
        for (size_t i = 0; i < sino.size(); i++)
            sino[i]->imprimir(npSino, i == sino.size() - 1);
    }
}

void NodoBucleRepetir::imprimir(const std::string& p, bool u) const {
    cabecera(p, u, BLU, "BucleRepetir");
    std::string np = hijoPrefijo(p, u);

    // Expresion de veces
    std::cout << DIM << np << RAMA << RST << BLU << BOLD << "Veces\n" << RST;
    veces->imprimir(np + VERT, true);

    // Cuerpo
    std::cout << DIM << np << ULTIMO << RST << BLU << BOLD << "Cuerpo\n" << RST;
    std::string npCuerpo = np + ESP;
    for (size_t i = 0; i < cuerpo.size(); i++)
        cuerpo[i]->imprimir(npCuerpo, i == cuerpo.size() - 1);
}

void NodoBucleMientras::imprimir(const std::string& p, bool u) const {
    cabecera(p, u, BLU, "BucleMientras");
    std::string np = hijoPrefijo(p, u);

    // Condicion
    std::cout << DIM << np << RAMA << RST << BLU << BOLD << "Condicion\n" << RST;
    condicion->imprimir(np + VERT, true);

    // Cuerpo
    std::cout << DIM << np << ULTIMO << RST << BLU << BOLD << "Cuerpo\n" << RST;
    std::string npCuerpo = np + ESP;
    for (size_t i = 0; i < cuerpo.size(); i++)
        cuerpo[i]->imprimir(npCuerpo, i == cuerpo.size() - 1);
}

void NodoMostrar::imprimir(const std::string& p, bool u) const {
    cabecera(p, u, CYN, "Mostrar");
    expresion->imprimir(hijoPrefijo(p, u), true);
}

// -----------------------------------------------------------------------
// Nodo raiz
// -----------------------------------------------------------------------
void NodoPrograma::imprimir(const std::string&, bool) const {
    std::cout << BLU << BOLD << "Programa\n" << RST;
    for (size_t i = 0; i < instrucciones.size(); i++)
        instrucciones[i]->imprimir("", i == instrucciones.size() - 1);
}
