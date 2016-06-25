package main

import (
	"log"
	"net/http"
	"todos"
)

func main() {
	http.HandleFunc("/", func(rw http.ResponseWriter, req *http.Request) {
		http.ServeFile(rw, req, "frontend/index.html")
	})
	http.Handle("/todos", todos.TodosImpl)
	log.Println("Listening on :8081...")
	log.Fatal(http.ListenAndServe(":8081", nil))
}
