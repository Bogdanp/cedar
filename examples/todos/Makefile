SOURCE="todos.cedar"
SERVER="backend/src/todos/todos.go"
CLIENT="frontend/src/Api/Todos.elm"
GO_SOURCES=$(shell find backend/src/ -type f -name "*.go" -print)
ELM_SOURCES=$(shell find frontend/src/ -type f -name "*.elm" -print)

.PHONY: build

serve: build
	backend/bin/backend

build: $(SERVER) $(CLIENT) $(GO_SOURCES) $(ELM_SOURCES)
	cd backend && gb build all
	cd frontend && elm package install -y && elm make src/Main.elm --output=index.html

$(SERVER): todos.cedar
	cedar generate go --package-name todos --server-name Todos $(SOURCE) > $(SERVER)

$(CLIENT): todos.cedar
	mkdir -p frontend/src/Api
	cedar generate elm --module-name "Api.Todos" $(SOURCE) > $(CLIENT)
