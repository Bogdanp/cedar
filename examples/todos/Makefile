SOURCE=todos.cedar
BIN=backend/bin/backend
SERVER=backend/src/todos/todos.go
INDEX=frontend/index.html
CLIENT=frontend/src/Api/Todos.elm
GO_SOURCES=$(shell find backend/src -type f -name "*.go" -print)
ELM_SOURCES=$(shell find frontend/src -type f -name "*.elm" -print)

.PHONY: all

all: $(BIN)
	$(shell ./backend/bin/backend)

$(BIN): $(INDEX) $(SERVER) $(GO_SOURCES)
	cd backend && gb build backend

$(INDEX): $(CLIENT) $(ELM_SOURCES)
	cd frontend && elm package install -y && elm make src/Main.elm --output=index.html

$(SERVER): $(SOURCE)
	cedar generate go --package-name todos --server-name Todos $(SOURCE) > $(SERVER)

$(CLIENT): $(SOURCE)
	mkdir -p frontend/src/Api
	cedar generate elm --module-name "Api.Todos" $(SOURCE) > $(CLIENT)
