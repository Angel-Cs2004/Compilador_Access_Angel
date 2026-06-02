#include <iostream>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <string>
#include <vector>
#include <cstdio>   // sscanf
#include "lexer.hpp"
#include "parser.hpp"
#include "semantico.hpp"
#include "codintermedio.hpp"
#include "optimizador.hpp"
#include "generador.hpp"

// -----------------------------------------------------------------------
// Colores ANSI
// -----------------------------------------------------------------------
namespace Col {
    const std::string RST  = "\033[0m";
    const std::string BOLD = "\033[1m";
    const std::string DIM  = "\033[2m";
    const std::string RED  = "\033[31m";
    const std::string GRN  = "\033[32m";
    const std::string YEL  = "\033[33m";
    const std::string BLU  = "\033[34m";
    const std::string MAG  = "\033[35m";
    const std::string CYN  = "\033[36m";
    const std::string WHT  = "\033[37m";
}

// -----------------------------------------------------------------------
// Utilidades de cadena
// -----------------------------------------------------------------------
static std::vector<std::string> dividirLineas(const std::string& fuente) {
    std::vector<std::string> lineas;
    std::istringstream ss(fuente);
    std::string linea;
    while (std::getline(ss, linea)) lineas.push_back(linea);
    return lineas;
}

// Extrae linea y columna del formato "[Linea X, Col Y] ..."
static bool extraerPosicion(const std::string& err, int& linea, int& col) {
    return std::sscanf(err.c_str(), "[Linea %d, Col %d]", &linea, &col) == 2;
}

// -----------------------------------------------------------------------
// Muestra error/advertencia con linea fuente y puntero ^ (estilo gcc/clang)
// -----------------------------------------------------------------------
static void mostrarAdvertenciaConContexto(const std::string& warn,
                                           const std::vector<std::string>& lineas,
                                           const std::string& prefijo = "  ") {
    int linea = -1, col = -1;
    extraerPosicion(warn, linea, col);

    std::cout << prefijo << Col::YEL << Col::BOLD << "Advertencia: " << Col::RST
              << Col::YEL << warn << Col::RST << "\n";

    if (linea > 0 && linea <= static_cast<int>(lineas.size())) {
        const std::string& src = lineas[linea - 1];
        std::cout << prefijo
                  << Col::DIM << std::setw(4) << linea << " | " << Col::RST
                  << src << "\n";
        if (col > 0) {
            std::string sangria(prefijo.size() + 7, ' ');
            std::string espacio(static_cast<size_t>(col - 1), ' ');
            std::cout << sangria << espacio
                      << Col::YEL << Col::BOLD << "^" << Col::RST << "\n";
        }
    }
    std::cout << "\n";
}

static void mostrarErrorConContexto(const std::string& err,
                                     const std::vector<std::string>& lineas,
                                     const std::string& prefijo = "  ") {
    int linea = -1, col = -1;
    extraerPosicion(err, linea, col);

    std::cout << prefijo << Col::RED << Col::BOLD << err << Col::RST << "\n";

    if (linea > 0 && linea <= static_cast<int>(lineas.size())) {
        const std::string& src = lineas[linea - 1];
        std::cout << prefijo
                  << Col::DIM << std::setw(4) << linea << " | " << Col::RST
                  << src << "\n";

        if (col > 0) {
            std::string sangria(prefijo.size() + 7, ' ');
            std::string espacio(static_cast<size_t>(col - 1), ' ');
            std::cout << sangria << espacio
                      << Col::RED << Col::BOLD << "^" << Col::RST << "\n";
        }
    }
    std::cout << "\n";
}

// -----------------------------------------------------------------------
// Tabla de tokens (fase 1)
// -----------------------------------------------------------------------
static const std::string& colorDeToken(const Token& t) {
    const std::string cat = t.categoriaColor();
    if (cat == "keyword")       return Col::BLU;
    if (cat == "operador")      return Col::YEL;
    if (cat == "literal")       return Col::GRN;
    if (cat == "identificador") return Col::CYN;
    if (cat == "error")         return Col::RED;
    return Col::WHT;
}

static void imprimirTablaTokens(const std::vector<Token>& tokens) {
    const int WT = 16, WV = 22, WL = 6, WC = 8;
    const std::string sep = "+" + std::string(WT+2,'-') + "+"
                                + std::string(WV+2,'-') + "+"
                                + std::string(WL+2,'-') + "+"
                                + std::string(WC+2,'-') + "+";

    auto fila = [&](const std::string& a, const std::string& b,
                    const std::string& c, const std::string& d,
                    const std::string& color) {
        std::cout << "| " << color << std::left << std::setw(WT) << a << Col::RST
                  << " | " << color << std::setw(WV) << b << Col::RST
                  << " | " << std::setw(WL) << c
                  << " | " << std::setw(WC) << d << " |\n";
    };

    std::cout << Col::BOLD << sep << Col::RST << "\n";
    fila("TIPO", "VALOR", "LINEA", "COLUMNA", Col::BOLD);
    std::cout << Col::BOLD << sep << Col::RST << "\n";

    int n = 0;
    for (const auto& tok : tokens) {
        if (tok.tipo == TipoToken::NUEVA_LINEA || tok.tipo == TipoToken::FIN_ARCHIVO) continue;
        std::string val = tok.valor;
        if (val.size() > static_cast<size_t>(WV)) val = val.substr(0, WV-3) + "...";
        fila(tok.nombreTipo(), val,
             std::to_string(tok.linea), std::to_string(tok.columna),
             colorDeToken(tok));
        n++;
    }
    std::cout << Col::BOLD << sep << Col::RST << "\n";
    std::cout << "\n" << Col::BOLD << "Tokens: " << Col::RST << n << "\n";
}

// -----------------------------------------------------------------------
// Reporte final de compilacion
// -----------------------------------------------------------------------
static void imprimirReporte(const std::string& archivo,
                             int totalLineas,
                             int totalTokens,
                             int erroresLexicos,
                             int erroresSintacticos,
                             int erroresSemanticos,
                             int advertencias,
                             int nodos,
                             int instrIR         = 0,
                             int instrOptimizadas = 0,
                             bool codigoGenerado  = false) {
    bool ok = (erroresLexicos == 0 && erroresSintacticos == 0 && erroresSemanticos == 0);
    int totalErrores = erroresLexicos + erroresSintacticos + erroresSemanticos;

    std::cout << "\n" << Col::BOLD
              << "+------------------------------------------+\n"
              << "|          REPORTE DE COMPILACION          |\n"
              << "+------------------------------------------+\n"
              << Col::RST;

    auto fila = [](const std::string& clave, const std::string& val,
                   const std::string& color = "") {
        std::cout << "  " << std::left << std::setw(28) << clave
                  << color << val << Col::RST << "\n";
    };

    fila("Archivo:",             archivo);
    fila("Lineas analizadas:",   std::to_string(totalLineas));
    fila("Tokens encontrados:",  std::to_string(totalTokens));
    fila("Nodos AST:",           std::to_string(nodos));
    fila("Errores lexicos:",     std::to_string(erroresLexicos),
         erroresLexicos     > 0 ? Col::RED : Col::GRN);
    fila("Errores sintacticos:", std::to_string(erroresSintacticos),
         erroresSintacticos > 0 ? Col::RED : Col::GRN);
    fila("Errores semanticos:",  std::to_string(erroresSemanticos),
         erroresSemanticos  > 0 ? Col::RED : Col::GRN);
    if (advertencias > 0)
        fila("Advertencias:",    std::to_string(advertencias), Col::YEL);
    if (instrIR > 0) {
        fila("Instrucciones IR:", std::to_string(instrIR));
        if (instrOptimizadas > 0)
            fila("Instrucciones eliminadas:", std::to_string(instrOptimizadas), Col::YEL);
    }
    if (codigoGenerado)
        fila("Codigo Python:", "generado", Col::GRN);

    std::cout << "  " << std::string(40, '-') << "\n";
    if (ok) {
        std::cout << "  " << Col::GRN << Col::BOLD
                  << "ESTADO: COMPILACION EXITOSA" << Col::RST << "\n";
    } else {
        std::cout << "  " << Col::RED << Col::BOLD
                  << "ESTADO: COMPILACION FALLIDA  "
                  << "(" << totalErrores << " error(es))"
                  << Col::RST << "\n";
    }
    std::cout << "+------------------------------------------+\n\n";
}

// -----------------------------------------------------------------------
// Separador de seccion
// -----------------------------------------------------------------------
static void separador(const std::string& titulo) {
    std::cout << "\n" << Col::BOLD << Col::CYN
              << "==========================================\n"
              << "  " << titulo << "\n"
              << "==========================================\n"
              << Col::RST << "\n";
}

// -----------------------------------------------------------------------
// Banner de bienvenida
// -----------------------------------------------------------------------
static void banner(const std::string& archivo) {
    std::cout << "\n" << Col::BLU << Col::BOLD
              << "  ╔══════════════════════════════════════╗\n"
              << "  ║     COMPILADOR ACCESIBLE v0.4        ║\n"
              << "  ║  Lexico + Sint. + Sem. + IR + Gen.  ║\n"
              << "  ╚══════════════════════════════════════╝\n"
              << Col::RST;
    std::cout << "  Archivo: " << Col::CYN << archivo << Col::RST << "\n\n";
}

// -----------------------------------------------------------------------
// Ayuda
// -----------------------------------------------------------------------
static void mostrarAyuda(const char* prog) {
    std::cout << Col::BOLD << "Uso:\n" << Col::RST
              << "  " << prog << " [opciones] [archivo.acc]\n\n"
              << Col::BOLD << "Opciones de visualizacion:\n" << Col::RST
              << "  (ninguna)          Ejecuta todas las fases y muestra el AST\n"
              << "  --tokens  -t       Solo muestra la tabla de tokens (fase 1)\n"
              << "  --ast     -a       Solo muestra el AST (fase 2)\n"
              << "  --ir      -i       Muestra el codigo intermedio TAC (fase 4)\n"
              << "  --gen     -g       Muestra el codigo Python generado (fase 6)\n"
              << "  --check   -c       Valida sin mostrar salida detallada\n"
              << "  --help    -h       Muestra esta ayuda\n\n"
              << Col::BOLD << "Opciones de salida:\n" << Col::RST
              << "  --salida <arch>    Escribe el codigo Python generado en archivo\n\n"
              << Col::BOLD << "Ejemplos:\n" << Col::RST
              << "  " << prog << " ejemplos/completo.acc\n"
              << "  " << prog << " --tokens   ejemplos/basico.acc\n"
              << "  " << prog << " --ir       ejemplos/completo.acc\n"
              << "  " << prog << " --gen      ejemplos/completo.acc\n"
              << "  " << prog << " --salida   salida.py ejemplos/completo.acc\n"
              << "  " << prog << " --check    ejemplos/errores_sint.acc\n\n";
}

// -----------------------------------------------------------------------
// main
// -----------------------------------------------------------------------
int main(int argc, char* argv[]) {
    std::string fuente;
    std::string nombreArchivo = "<interactivo>";
    std::string archivoSalida;
    bool soloTokens  = false;
    bool soloAST     = false;
    bool mostrarIR   = false;
    bool mostrarGen  = false;
    bool modoCheck   = false;

    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "--tokens"  || arg == "-t") { soloTokens = true; continue; }
        if (arg == "--ast"     || arg == "-a") { soloAST    = true; continue; }
        if (arg == "--ir"      || arg == "-i") { mostrarIR  = true; continue; }
        if (arg == "--gen"     || arg == "-g") { mostrarGen = true; continue; }
        if (arg == "--check"   || arg == "-c") { modoCheck  = true; continue; }
        if (arg == "--help"    || arg == "-h") { mostrarAyuda(argv[0]); return 0; }
        if (arg == "--salida") {
            if (i + 1 < argc) { archivoSalida = argv[++i]; continue; }
            std::cerr << Col::RED << "Error: --salida requiere un nombre de archivo\n" << Col::RST;
            return 1;
        }

        nombreArchivo = arg;
        std::ifstream archivo(arg);
        if (!archivo.is_open()) {
            std::cerr << Col::RED << "Error: No se pudo abrir '" << arg << "'" << Col::RST << "\n";
            return 1;
        }
        std::ostringstream ss;
        ss << archivo.rdbuf();
        fuente = ss.str();
    }

    // Modo interactivo
    if (fuente.empty() && nombreArchivo == "<interactivo>") {
        std::cout << Col::BOLD << Col::CYN
                  << "=== Compilador Accesible — Modo Interactivo ===\n"
                  << Col::RST
                  << "Escribe el codigo. Linea vacia para terminar.\n\n";
        std::string linea;
        while (std::getline(std::cin, linea)) {
            if (linea.empty()) break;
            fuente += linea + "\n";
        }
    }

    auto lineasFuente = dividirLineas(fuente);

    // Si --salida esta presente, --gen se activa automaticamente
    if (!archivoSalida.empty()) mostrarGen = true;

    bool mostrarTokensFlag = !soloAST && !modoCheck && !mostrarIR && !mostrarGen;
    bool mostrarASTFlag    = !soloTokens && !modoCheck && !mostrarIR && !mostrarGen;

    if (!modoCheck) banner(nombreArchivo);

    // ---- FASE 1: Analizador Lexico ----
    if (mostrarTokensFlag) {
        separador("FASE 1 — ANALISIS LEXICO");
        std::cout << "Leyenda: "
                  << Col::BLU << "palabra clave" << Col::RST << "  "
                  << Col::YEL << "operador"       << Col::RST << "  "
                  << Col::GRN << "literal"         << Col::RST << "  "
                  << Col::CYN << "identificador"   << Col::RST << "\n\n";
    }

    Lexer lexer(fuente);
    auto tokens = lexer.tokenizar();

    if (mostrarTokensFlag) imprimirTablaTokens(tokens);

    int totalTokens = 0;
    for (const auto& t : tokens)
        if (t.tipo != TipoToken::NUEVA_LINEA && t.tipo != TipoToken::FIN_ARCHIVO)
            totalTokens++;

    if (lexer.tieneErrores()) {
        if (!modoCheck) {
            std::cout << "\n" << Col::RED << Col::BOLD
                      << "ERRORES LEXICOS:\n" << Col::RST;
            for (const auto& e : lexer.errores())
                mostrarErrorConContexto(e, lineasFuente);
        }
        imprimirReporte(nombreArchivo,
                        static_cast<int>(lineasFuente.size()), totalTokens,
                        static_cast<int>(lexer.errores().size()), 0, 0, 0, 0);
        return 1;
    }

    if (mostrarTokensFlag)
        std::cout << "\n" << Col::GRN << "Analisis lexico: OK\n" << Col::RST;

    // ---- FASE 2: Analizador Sintactico ----
    Parser parser(tokens);

    if (mostrarASTFlag) separador("FASE 2 — ANALISIS SINTACTICO (AST)");

    auto ast = parser.parsear();

    if (mostrarASTFlag) ast->imprimir();

    if (parser.tieneErrores()) {
        if (!modoCheck) {
            std::cout << "\n" << Col::RED << Col::BOLD
                      << "ERRORES SINTACTICOS:\n" << Col::RST;
            for (const auto& e : parser.errores())
                mostrarErrorConContexto(e, lineasFuente);
        }
        imprimirReporte(nombreArchivo,
                        static_cast<int>(lineasFuente.size()), totalTokens,
                        0, static_cast<int>(parser.errores().size()), 0, 0,
                        static_cast<int>(ast->instrucciones.size()));
        return 1;
    }

    // ---- FASE 3: Analizador Semantico ----
    AnalizadorSemantico semantico;
    semantico.analizar(*ast);

    if (mostrarASTFlag || modoCheck) {
        if (mostrarASTFlag) {
            separador("FASE 3 — ANALISIS SEMANTICO");

            if (!semantico.tieneAdvertencias() && !semantico.tieneErrores())
                std::cout << Col::GRN << "  Sin errores semanticos.\n" << Col::RST << "\n";

            if (semantico.tieneAdvertencias()) {
                std::cout << Col::YEL << Col::BOLD << "ADVERTENCIAS:\n" << Col::RST;
                for (const auto& w : semantico.advertencias())
                    mostrarAdvertenciaConContexto(w, lineasFuente);
            }

            if (semantico.tieneErrores()) {
                std::cout << Col::RED << Col::BOLD << "ERRORES SEMANTICOS:\n" << Col::RST;
                for (const auto& e : semantico.errores())
                    mostrarErrorConContexto(e, lineasFuente);
            }
        }
    }

    if (semantico.tieneErrores()) {
        imprimirReporte(nombreArchivo,
                        static_cast<int>(lineasFuente.size()), totalTokens,
                        0, 0, static_cast<int>(semantico.errores().size()),
                        static_cast<int>(semantico.advertencias().size()),
                        static_cast<int>(ast->instrucciones.size()));
        return 1;
    }

    // ---- FASE 4: Generacion de Codigo Intermedio (TAC) ----
    GeneradorIR generadorIR;
    auto codigoIR = generadorIR.generar(*ast);

    // ---- FASE 5: Optimizacion ----
    Optimizador optimizador;
    auto codigoOpt = optimizador.optimizar(codigoIR);

    if (mostrarIR) {
        separador("FASE 4 — CODIGO INTERMEDIO (TAC)");
        GeneradorIR::imprimir(codigoIR);

        separador("FASE 5 — CODIGO INTERMEDIO OPTIMIZADO");
        if (optimizador.instruccionesEliminadas() > 0)
            std::cout << Col::YEL << "  Instrucciones eliminadas: "
                      << optimizador.instruccionesEliminadas() << Col::RST << "\n\n";
        else
            std::cout << Col::GRN << "  No se encontraron optimizaciones adicionales.\n" << Col::RST << "\n";
        GeneradorIR::imprimir(codigoOpt);
    }

    // ---- FASE 6: Generacion de Codigo Python ----
    bool codigoPythonGenerado = false;
    std::string codigoPython;

    if (mostrarGen || !archivoSalida.empty()) {
        GeneradorPython generadorPy;
        codigoPython = generadorPy.generar(*ast);
        codigoPythonGenerado = true;

        if (mostrarGen && archivoSalida.empty()) {
            separador("FASE 6 — CODIGO PYTHON GENERADO");
            std::cout << Col::GRN << codigoPython << Col::RST;
        }

        if (!archivoSalida.empty()) {
            std::ofstream salida(archivoSalida);
            if (salida.is_open()) {
                salida << codigoPython;
                salida.close();
                separador("FASE 6 — CODIGO PYTHON GENERADO");
                std::cout << Col::GRN << codigoPython << Col::RST;
                std::cout << Col::GRN << Col::BOLD
                          << "  Archivo escrito: " << archivoSalida << Col::RST << "\n\n";
            } else {
                std::cerr << Col::RED << "Error: No se pudo escribir en '"
                          << archivoSalida << "'" << Col::RST << "\n";
            }
        }
    }

    imprimirReporte(nombreArchivo,
                    static_cast<int>(lineasFuente.size()), totalTokens,
                    0, 0,
                    static_cast<int>(semantico.errores().size()),
                    static_cast<int>(semantico.advertencias().size()),
                    static_cast<int>(ast->instrucciones.size()),
                    static_cast<int>(codigoIR.size()),
                    optimizador.instruccionesEliminadas(),
                    codigoPythonGenerado);

    return 0;
}
