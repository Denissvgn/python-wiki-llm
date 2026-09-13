package main

import (
	"log"
	"net/http"
)

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", health)
	log.Fatal(http.ListenAndServe(":8080", mux))
}
