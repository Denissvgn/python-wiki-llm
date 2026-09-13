package main

import (
	"fmt"
	"net/http"

	"example.org/llm-wiki/go-http/internal/store"
)

func health(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintln(w, store.Status())
}
