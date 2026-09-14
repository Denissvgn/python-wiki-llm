// Package store supplies the health message without external services.
package store

type Store struct{}

func (s Store) status() string {
	return "ready"
}

// Status returns the current health message.
func Status() string {
	s := Store{}
	return s.status()
}
