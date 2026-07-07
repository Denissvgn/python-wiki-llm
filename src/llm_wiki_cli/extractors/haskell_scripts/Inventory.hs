module Inventory
    ( ClassInfo (..)
    , FileEntry (..)
    , FunctionInfo (..)
    , ImportInfo (..)
    , Inventory
    , emptyFileEntry
    ) where

type Inventory = [(FilePath, FileEntry)]

data FileEntry = FileEntry
    { fileLanguage :: String
    , fileModule :: Maybe String
    , fileLanguagePragmas :: [String]
    , fileImports :: [ImportInfo]
    , fileClasses :: [ClassInfo]
    , fileFunctions :: [FunctionInfo]
    }
    deriving (Eq, Show)

data ImportInfo = ImportInfo
    { importModule :: String
    , importQualified :: Bool
    , importAlias :: Maybe String
    , importLine :: Int
    }
    deriving (Eq, Show)

data FunctionInfo = FunctionInfo
    { functionName :: String
    , functionKind :: String
    , functionSignature :: Maybe String
    , functionLine :: Int
    }
    deriving (Eq, Show)

data ClassInfo = ClassInfo
    { className :: String
    , classKind :: String
    , classLine :: Int
    }
    deriving (Eq, Show)

emptyFileEntry :: FileEntry
emptyFileEntry =
    FileEntry
        { fileLanguage = "haskell"
        , fileModule = Nothing
        , fileLanguagePragmas = []
        , fileImports = []
        , fileClasses = []
        , fileFunctions = []
        }
