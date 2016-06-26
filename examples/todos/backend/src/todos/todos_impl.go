package todos

import (
	"errors"
	"net/http"
	"sync"
)

// TodosImpl implements a Todos service.
var TodosImpl Todos

var mu sync.Mutex
var seq int
var todos map[int]Todo

func init() {
	todos = make(map[int]Todo)

	TodosImpl = Todos{}
	TodosImpl.HandleGetTodos(getTodos)
	TodosImpl.HandleGetTodo(getTodo)
	TodosImpl.HandleAddTodo(addTodo)
	TodosImpl.HandleDeleteTodo(deleteTodo)
}

func getTodos(req *http.Request, data *GetTodosRequest) ([]Todo, error) {
	mu.Lock()
	i := 0
	xs := make([]Todo, len(todos))
	for _, todo := range todos {
		xs[i] = todo
		i++
	}
	mu.Unlock()

	return xs, nil
}

func getTodo(req *http.Request, data *GetTodoRequest) (*Todo, error) {
	mu.Lock()
	todo, ok := todos[data.ID]
	mu.Unlock()

	if !ok {
		return nil, errors.New("todo not found")
	}

	return &todo, nil
}

func addTodo(req *http.Request, data *AddTodoRequest) (Todo, error) {
	mu.Lock()
	seq++
	todo := Todo{seq, data.Deadline, data.Description, StatusTodo}
	todos[seq] = todo
	mu.Unlock()

	return todo, nil
}

func deleteTodo(req *http.Request, data *DeleteTodoRequest) (Unit, error) {
	mu.Lock()
	delete(todos, data.ID)
	mu.Unlock()

	return Unit{}, nil
}
