package main

import (
	"log"
	"net/http"

	"server"
)

func main() {
	http.Handle("/echo", server.EchoImpl)
	log.Println("Listening on :9090")
	log.Fatal(http.ListenAndServe(":9090", nil))
}
