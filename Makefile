CXX      = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -Wpedantic -O2
TARGET   = compilador
SRCDIR   = src
SRCS     = $(SRCDIR)/main.cpp \
           $(SRCDIR)/token.cpp \
           $(SRCDIR)/lexer.cpp \
           $(SRCDIR)/ast.cpp \
           $(SRCDIR)/parser.cpp
OBJS     = $(SRCS:.cpp=.o)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) -o $@ $^

$(SRCDIR)/%.o: $(SRCDIR)/%.cpp
	$(CXX) $(CXXFLAGS) -c -o $@ $<

# Solo tokens (fase 1)
tokens: $(TARGET)
	./$(TARGET) --tokens ejemplos/completo.acc

# Solo AST (fase 2)
ast: $(TARGET)
	./$(TARGET) --ast ejemplos/completo.acc

# Ambas fases
test: $(TARGET)
	@echo "" && echo ">>> Prueba 1: basico.acc"
	./$(TARGET) ejemplos/basico.acc
	@echo "" && echo ">>> Prueba 2: condicion.acc"
	./$(TARGET) ejemplos/condicion.acc
	@echo "" && echo ">>> Prueba 3: completo.acc"
	./$(TARGET) ejemplos/completo.acc
	@echo "" && echo ">>> Prueba 4: errores.acc (debe mostrar errores)"
	./$(TARGET) ejemplos/errores.acc; true

run: $(TARGET)
	./$(TARGET)

clean:
	rm -f $(OBJS) $(TARGET)

.PHONY: all tokens ast test run clean
