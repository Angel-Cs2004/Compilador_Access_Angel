CXX      = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -Wpedantic -O2

SRCDIR   = src
BUILDDIR = build
TARGET   = $(BUILDDIR)/compilador

SRCS     = $(SRCDIR)/main.cpp \
           $(SRCDIR)/token.cpp \
           $(SRCDIR)/lexer.cpp \
           $(SRCDIR)/ast.cpp \
           $(SRCDIR)/parser.cpp
OBJS     = $(patsubst $(SRCDIR)/%.cpp, $(BUILDDIR)/%.o, $(SRCS))

# ── Compilacion ─────────────────────────────────────────────────────────────
all: $(BUILDDIR) $(TARGET)

$(BUILDDIR):
	mkdir -p $(BUILDDIR)

$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) -o $@ $^

$(BUILDDIR)/%.o: $(SRCDIR)/%.cpp
	$(CXX) $(CXXFLAGS) -c -o $@ $<

# ── Ejecucion ────────────────────────────────────────────────────────────────
run: all
	./$(TARGET)

# ── Tests con ejemplos ────────────────────────────────────────────────────────
test: all
	@echo "" && echo ">>> Validos: basico"
	./$(TARGET) ejemplos/validos/basico.acc
	@echo "" && echo ">>> Validos: condicion"
	./$(TARGET) ejemplos/validos/condicion.acc
	@echo "" && echo ">>> Validos: completo"
	./$(TARGET) ejemplos/validos/completo.acc
	@echo "" && echo ">>> Errores: errores_lex (esperado: errores lexicos)"
	./$(TARGET) ejemplos/errores/errores_lex.acc; true
	@echo "" && echo ">>> Errores: errores_sint (esperado: errores sintacticos)"
	./$(TARGET) ejemplos/errores/errores_sint.acc; true

tokens: all
	./$(TARGET) --tokens ejemplos/validos/completo.acc

ast: all
	./$(TARGET) --ast ejemplos/validos/completo.acc

check: all
	@echo "--- Validos ---"
	./$(TARGET) --check ejemplos/validos/basico.acc
	./$(TARGET) --check ejemplos/validos/condicion.acc
	./$(TARGET) --check ejemplos/validos/completo.acc
	@echo "--- Errores ---"
	./$(TARGET) --check ejemplos/errores/errores_lex.acc;  true
	./$(TARGET) --check ejemplos/errores/errores_sint.acc; true

# ── Limpieza ─────────────────────────────────────────────────────────────────
clean:
	rm -f $(OBJS) $(TARGET)

.PHONY: all run test tokens ast check clean
