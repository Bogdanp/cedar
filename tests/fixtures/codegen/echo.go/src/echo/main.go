package main

import (
	"log"
	"net/http"

	"server"
)

func main() {
	http.Handle("/echo", server.EchoImpl)
	log.Fatal(http.ListenAndServe(":9090", nil))
}
