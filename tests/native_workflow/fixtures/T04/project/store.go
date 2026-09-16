package hooks

type Store struct { Hook func(string) string }
func (s *Store) Handle(value string) string { return s.Hook(value) }
