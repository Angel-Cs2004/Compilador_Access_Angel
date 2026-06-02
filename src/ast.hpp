#pragma once
#include <string>
#include <vector>
#include <memory>

struct Nodo;
using NodoPtr = std::unique_ptr<Nodo>;

// -----------------------------------------------------------------------
// Clase base — todos los nodos del AST heredan de aqui
// -----------------------------------------------------------------------
struct Nodo {
    int linea   = -1;
    int columna = -1;
    virtual ~Nodo() = default;
    virtual std::string tipoNodo() const = 0;
    // prefijo: cadena de indentacion acumulada
    // esUltimo: si es el ultimo hijo de su padre (cambia el conector del arbol)
    virtual void imprimir(const std::string& prefijo = "", bool esUltimo = true) const = 0;
};

// -----------------------------------------------------------------------
// Expresiones
// -----------------------------------------------------------------------
struct NodoNumero : Nodo {
    double valor;
    explicit NodoNumero(double v) : valor(v) {}
    std::string tipoNodo() const override { return "Numero"; }
    void imprimir(const std::string& prefijo, bool esUltimo) const override;
};

struct NodoTexto : Nodo {
    std::string valor;
    explicit NodoTexto(std::string v) : valor(std::move(v)) {}
    std::string tipoNodo() const override { return "Texto"; }
    void imprimir(const std::string& prefijo, bool esUltimo) const override;
};

struct NodoBooleano : Nodo {
    bool valor;
    explicit NodoBooleano(bool v) : valor(v) {}
    std::string tipoNodo() const override { return "Booleano"; }
    void imprimir(const std::string& prefijo, bool esUltimo) const override;
};

struct NodoIdentificador : Nodo {
    std::string nombre;
    explicit NodoIdentificador(std::string n) : nombre(std::move(n)) {}
    std::string tipoNodo() const override { return "Identificador"; }
    void imprimir(const std::string& prefijo, bool esUltimo) const override;
};

struct NodoOpBinaria : Nodo {
    NodoPtr     izquierda;
    std::string operador; // "mas" | "menos" | "por" | "entre"
    NodoPtr     derecha;
    NodoOpBinaria(NodoPtr iz, std::string op, NodoPtr de)
        : izquierda(std::move(iz)), operador(std::move(op)), derecha(std::move(de)) {}
    std::string tipoNodo() const override { return "OpBinaria"; }
    void imprimir(const std::string& prefijo, bool esUltimo) const override;
};

// -----------------------------------------------------------------------
// Condiciones
// -----------------------------------------------------------------------
struct NodoComparacion : Nodo {
    NodoPtr     izquierda;
    std::string comparador; // "es igual a" | "es mayor que" | etc.
    NodoPtr     derecha;
    NodoComparacion(NodoPtr iz, std::string comp, NodoPtr de)
        : izquierda(std::move(iz)), comparador(std::move(comp)), derecha(std::move(de)) {}
    std::string tipoNodo() const override { return "Comparacion"; }
    void imprimir(const std::string& prefijo, bool esUltimo) const override;
};

struct NodoOpLogica : Nodo {
    NodoPtr     izquierda;
    std::string operador; // "y" | "o"
    NodoPtr     derecha;
    NodoOpLogica(NodoPtr iz, std::string op, NodoPtr de)
        : izquierda(std::move(iz)), operador(std::move(op)), derecha(std::move(de)) {}
    std::string tipoNodo() const override { return "OpLogica"; }
    void imprimir(const std::string& prefijo, bool esUltimo) const override;
};

struct NodoNegar : Nodo {
    NodoPtr operando;
    explicit NodoNegar(NodoPtr op) : operando(std::move(op)) {}
    std::string tipoNodo() const override { return "Negar"; }
    void imprimir(const std::string& prefijo, bool esUltimo) const override;
};

// -----------------------------------------------------------------------
// Instrucciones
// -----------------------------------------------------------------------
struct NodoDeclaracion : Nodo {
    std::string nombre;
    NodoPtr     expresion;
    NodoDeclaracion(std::string n, NodoPtr expr)
        : nombre(std::move(n)), expresion(std::move(expr)) {}
    std::string tipoNodo() const override { return "Declaracion"; }
    void imprimir(const std::string& prefijo, bool esUltimo) const override;
};

struct NodoCondicional : Nodo {
    NodoPtr              condicion;
    std::vector<NodoPtr> entonces;
    std::vector<NodoPtr> sino;
    std::string tipoNodo() const override { return "Condicional"; }
    void imprimir(const std::string& prefijo, bool esUltimo) const override;
};

struct NodoBucleRepetir : Nodo {
    NodoPtr              veces;
    std::vector<NodoPtr> cuerpo;
    std::string tipoNodo() const override { return "BucleRepetir"; }
    void imprimir(const std::string& prefijo, bool esUltimo) const override;
};

struct NodoBucleMientras : Nodo {
    NodoPtr              condicion;
    std::vector<NodoPtr> cuerpo;
    std::string tipoNodo() const override { return "BucleMientras"; }
    void imprimir(const std::string& prefijo, bool esUltimo) const override;
};

struct NodoMostrar : Nodo {
    NodoPtr expresion;
    explicit NodoMostrar(NodoPtr expr) : expresion(std::move(expr)) {}
    std::string tipoNodo() const override { return "Mostrar"; }
    void imprimir(const std::string& prefijo, bool esUltimo) const override;
};

// -----------------------------------------------------------------------
// Nodo raiz del programa
// -----------------------------------------------------------------------
struct NodoPrograma : Nodo {
    std::vector<NodoPtr> instrucciones;
    std::string tipoNodo() const override { return "Programa"; }
    void imprimir(const std::string& prefijo = "", bool esUltimo = true) const override;
};
