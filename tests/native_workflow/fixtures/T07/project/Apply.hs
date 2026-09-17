module Apply where
apply :: (a -> b) -> a -> b
apply f x = f x
