module Json
    ( renderInventoryJson
    ) where

import Data.Char (ord)
import Data.List (intercalate, sortOn)
import Numeric (showHex)

import Inventory
    ( ClassInfo (..)
    , FileEntry (..)
    , FunctionInfo (..)
    , ImportInfo (..)
    , Inventory
    )

renderInventoryJson :: Inventory -> String
renderInventoryJson inventory =
    "{" ++ intercalate "," (map renderFile sortedInventory) ++ "}"
  where
    sortedInventory = sortOn fst inventory

renderFile :: (FilePath, FileEntry) -> String
renderFile (path, entry) =
    jsonString path ++ ":{" ++ intercalate "," fields ++ "}"
  where
    baseFields =
        [ ("language", jsonString (fileLanguage entry))
        , ("imports", renderList renderImport (fileImports entry))
        , ("classes", renderList renderClass (fileClasses entry))
        , ("functions", renderList renderFunction (fileFunctions entry))
        ]
    moduleFields =
        case fileModule entry of
            Nothing -> []
            Just moduleName -> [("module", jsonString moduleName)]
    pragmaFields =
        if null (fileLanguagePragmas entry)
            then []
            else
                [ ( "language_pragmas"
                  , renderList jsonString (fileLanguagePragmas entry)
                  )
                ]
    fields = map renderField (baseFields ++ moduleFields ++ pragmaFields)

renderField :: (String, String) -> String
renderField (name, value) = jsonString name ++ ":" ++ value

renderImport :: ImportInfo -> String
renderImport item =
    "{"
        ++ intercalate
            ","
            [ renderField ("module", jsonString (importModule item))
            , renderField ("qualified", jsonBool (importQualified item))
            , renderField ("alias", maybe "null" jsonString (importAlias item))
            , renderField ("line", show (importLine item))
            ]
        ++ "}"

renderClass :: ClassInfo -> String
renderClass item =
    "{"
        ++ intercalate
            ","
            [ renderField ("name", jsonString (className item))
            , renderField ("kind", jsonString (classKind item))
            , renderField ("line", show (classLine item))
            ]
        ++ "}"

renderFunction :: FunctionInfo -> String
renderFunction item =
    "{" ++ intercalate "," fields ++ "}"
  where
    baseFields =
        [ renderField ("name", jsonString (functionName item))
        , renderField ("kind", jsonString (functionKind item))
        ]
    signatureFields =
        case functionSignature item of
            Nothing -> []
            Just signature -> [renderField ("signature", jsonString signature)]
    lineFields = [renderField ("line", show (functionLine item))]
    fields = baseFields ++ signatureFields ++ lineFields

renderList :: (a -> String) -> [a] -> String
renderList renderItem values = "[" ++ intercalate "," (map renderItem values) ++ "]"

jsonBool :: Bool -> String
jsonBool True = "true"
jsonBool False = "false"

jsonString :: String -> String
jsonString value = "\"" ++ concatMap escapeChar value ++ "\""

escapeChar :: Char -> String
escapeChar '"' = "\\\""
escapeChar '\\' = "\\\\"
escapeChar '\b' = "\\b"
escapeChar '\f' = "\\f"
escapeChar '\n' = "\\n"
escapeChar '\r' = "\\r"
escapeChar '\t' = "\\t"
escapeChar char
    | ord char < 0x20 = "\\u" ++ leftPad 4 '0' (showHex (ord char) "")
    | otherwise = [char]

leftPad :: Int -> Char -> String -> String
leftPad width char value = replicate (max 0 (width - length value)) char ++ value
