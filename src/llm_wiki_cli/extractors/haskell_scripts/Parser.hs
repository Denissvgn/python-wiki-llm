{-# LANGUAGE PatternSynonyms #-}

module Parser
    ( parseSourceFile
    ) where

import Data.Char (isSpace)
import Data.List (isPrefixOf, sortOn)
import qualified GHC.Data.EnumSet as EnumSet
import GHC.Data.FastString (mkFastString)
import GHC.Data.StringBuffer (stringToStringBuffer)
import GHC.Hs
    ( ClsInstDecl (..)
    , DataDefnCons (..)
    , GhcPs
    , HsBindLR (..)
    , HsDataDefn (..)
    , HsDecl (..)
    , HsSigType (..)
    , HsModule (..)
    , HsWildCardBndrs (..)
    , ImportDecl (..)
    , InstDecl (..)
    , LHsDecl
    , LHsExpr
    , LHsSigWcType
    , LImportDecl
    , LPat
    , Match (..)
    , MatchGroup (..)
    , Pat (..)
    , Sig (..)
    , TyClDecl (..)
    , isImportDeclQualified
    )
import GHC.Parser (parseModule)
import GHC.Parser.Annotation (SrcSpanAnn', getLocA)
import GHC.Parser.Lexer
    ( ParseResult (..)
    , ParserOpts
    , getPsErrorMessages
    , initParserState
    , mkParserOpts
    , unP
    )
import GHC.Types.Name.Occurrence (occNameString)
import GHC.Types.Name.Reader (RdrName, rdrNameOcc)
import GHC.Types.SrcLoc
    ( GenLocated (..)
    , SrcSpan (..)
    , mkRealSrcLoc
    , srcSpanStartLine
    , unLoc
    )
import GHC.Unit.Module (moduleNameString)
import GHC.Types.Error (NoDiagnosticOpts (..))
import GHC.Utils.Error (DiagOpts (..), pprMessages)
import GHC.Utils.Outputable (Outputable, defaultSDocContext, ppr, showSDocUnsafe)
import System.FilePath (takeExtension)

import Inventory
    ( ClassInfo (..)
    , FileEntry (..)
    , FunctionInfo (..)
    , ImportInfo (..)
    , emptyFileEntry
    )

parseSourceFile :: FilePath -> FilePath -> IO (Either String FileEntry)
parseSourceFile absolutePath displayPath = do
    rawSource <- readFile absolutePath
    let source = prepareSource absolutePath rawSource
        parserState =
            initParserState
                parserOptions
                (stringToStringBuffer source)
                (mkRealSrcLoc (mkFastString displayPath) 1 1)
    pure $
        case unP parseModule parserState of
            POk _ parsedModule -> Right (moduleToEntry rawSource parsedModule)
            PFailed failedState ->
                Left
                    ( displayPath
                        ++ ": parse failed: "
                        ++ compactWhitespace
                            ( showSDocUnsafe
                                (pprMessages NoDiagnosticOpts (getPsErrorMessages failedState))
                            )
                    )

parserOptions :: ParserOpts
parserOptions =
    mkParserOpts EnumSet.empty diagOptions [] False False False True
  where
    diagOptions =
        DiagOpts
            EnumSet.empty
            EnumSet.empty
            False
            False
            Nothing
            defaultSDocContext

moduleToEntry :: String -> GenLocated location (HsModule GhcPs) -> FileEntry
moduleToEntry rawSource locatedModule =
    emptyFileEntry
        { fileModule = moduleName
        , fileLanguagePragmas = languagePragmas rawSource
        , fileImports = sortOn importLine imports
        , fileClasses = sortOn classLine classes
        , fileFunctions = sortOn functionLine functions
        }
  where
    parsedModule = unLoc locatedModule
    moduleName = moduleNameString . unLoc <$> hsmodName parsedModule
    imports = map importDeclToInfo (hsmodImports parsedModule)
    declarations = hsmodDecls parsedModule
    classes = concatMap declarationClasses declarations
    functions = concatMap declarationFunctions declarations

importDeclToInfo :: LImportDecl GhcPs -> ImportInfo
importDeclToInfo locatedImport =
    ImportInfo
        { importModule = moduleNameString (unLoc (ideclName importDecl))
        , importQualified = isImportDeclQualified (ideclQualified importDecl)
        , importAlias = moduleNameString . unLoc <$> ideclAs importDecl
        , importLine = lineFromLocatedA locatedImport
        }
  where
    importDecl = unLoc locatedImport

declarationClasses :: LHsDecl GhcPs -> [ClassInfo]
declarationClasses locatedDecl =
    case unLoc locatedDecl of
        TyClD _ tyCl -> tyClDeclarationToClass (lineFromLocatedA locatedDecl) tyCl
        InstD _ instDecl -> instanceDeclarationToClass (lineFromLocatedA locatedDecl) instDecl
        _ -> []

tyClDeclarationToClass :: Int -> TyClDecl GhcPs -> [ClassInfo]
tyClDeclarationToClass line tyCl =
    case tyCl of
        SynDecl {tcdLName = name} -> [classInfo "type" name]
        DataDecl {tcdLName = name, tcdDataDefn = dataDefn} ->
            [classInfo (dataDeclarationKind dataDefn) name]
        ClassDecl {tcdLName = name} -> [classInfo "class" name]
        _ -> []
  where
    classInfo kind name =
        ClassInfo
            { className = rdrNameText (unLoc name)
            , classKind = kind
            , classLine = line
            }

dataDeclarationKind :: HsDataDefn GhcPs -> String
dataDeclarationKind dataDefn =
    case dd_cons dataDefn of
        NewTypeCon _ -> "newtype"
        DataTypeCons _ _ -> "data"

instanceDeclarationToClass :: Int -> InstDecl GhcPs -> [ClassInfo]
instanceDeclarationToClass line instDecl =
    case instDecl of
        ClsInstD {cid_inst = classInstance} ->
            [ ClassInfo
                { className =
                    "instance "
                        ++ compactWhitespace (renderAst (cid_poly_ty classInstance))
                , classKind = "instance"
                , classLine = line
                }
            ]
        _ -> []

declarationFunctions :: LHsDecl GhcPs -> [FunctionInfo]
declarationFunctions locatedDecl =
    case unLoc locatedDecl of
        SigD _ sig -> signatureFunctions (lineFromLocatedA locatedDecl) sig
        ValD _ bind -> bindingFunctions (lineFromLocatedA locatedDecl) bind
        _ -> []

signatureFunctions :: Int -> Sig GhcPs -> [FunctionInfo]
signatureFunctions line sig =
    case sig of
        TypeSig _ names signature ->
            [ FunctionInfo
                { functionName = rdrNameText (unLoc name)
                , functionKind = "signature"
                , functionSignature = Just (renderSignature signature)
                , functionLine = line
                }
            | name <- names
            ]
        _ -> []

bindingFunctions :: Int -> HsBindLR GhcPs GhcPs -> [FunctionInfo]
bindingFunctions line bind =
    case bind of
        FunBind {fun_id = name, fun_matches = matches} ->
            [ FunctionInfo
                { functionName = rdrNameText (unLoc name)
                , functionKind = functionKindForMatches matches
                , functionSignature = Nothing
                , functionLine = line
                }
            ]
        PatBind {pat_lhs = patternValue} ->
            [ FunctionInfo
                { functionName = name
                , functionKind = "value"
                , functionSignature = Nothing
                , functionLine = line
                }
            | name <- patternNames patternValue
            ]
        VarBind {var_id = name} ->
            [ FunctionInfo
                { functionName = rdrNameText name
                , functionKind = "value"
                , functionSignature = Nothing
                , functionLine = line
                }
            ]
        _ -> []

functionKindForMatches :: MatchGroup GhcPs (LHsExpr GhcPs) -> String
functionKindForMatches matches =
    if any hasArguments (unLoc (mg_alts matches))
        then "function"
        else "value"
  where
    hasArguments locatedMatch = not (null (m_pats (unLoc locatedMatch)))

patternNames :: LPat GhcPs -> [String]
patternNames locatedPattern =
    case unLoc locatedPattern of
        VarPat _ name -> [rdrNameText (unLoc name)]
        LazyPat _ nested -> patternNames nested
        ParPat _ _ nested _ -> patternNames nested
        BangPat _ nested -> patternNames nested
        AsPat _ name _ nested -> rdrNameText (unLoc name) : patternNames nested
        SigPat _ nested _ -> patternNames nested
        _ -> []

renderSignature :: LHsSigWcType GhcPs -> String
renderSignature (HsWC _ locatedSignature) =
    let HsSig _ _ body = unLoc locatedSignature
     in compactWhitespace (renderAst body)

renderAst :: Outputable a => a -> String
renderAst = showSDocUnsafe . ppr

rdrNameText :: RdrName -> String
rdrNameText = occNameString . rdrNameOcc

lineFromLocatedA :: GenLocated (SrcSpanAnn' ann) value -> Int
lineFromLocatedA = lineFromSrcSpan . getLocA

lineFromSrcSpan :: SrcSpan -> Int
lineFromSrcSpan (RealSrcSpan span _) = srcSpanStartLine span
lineFromSrcSpan _ = 0

prepareSource :: FilePath -> String -> String
prepareSource path rawSource
    | takeExtension path == ".lhs" = preprocessLiterate rawSource
    | otherwise = rawSource

preprocessLiterate :: String -> String
preprocessLiterate source =
    unlines (processLines False (lines source))

processLines :: Bool -> [String] -> [String]
processLines _ [] = []
processLines inBlock (line : rest)
    | "\\begin{code}" `isPrefixOf` trimLeft line =
        "" : processLines True rest
    | "\\end{code}" `isPrefixOf` trimLeft line =
        "" : processLines False rest
    | inBlock = line : processLines True rest
    | Just code <- birdCode line = code : processLines False rest
    | otherwise = "" : processLines False rest

birdCode :: String -> Maybe String
birdCode ('>' : rest) = Just (dropOneLeadingSpace rest)
birdCode _ = Nothing

dropOneLeadingSpace :: String -> String
dropOneLeadingSpace (' ' : rest) = rest
dropOneLeadingSpace value = value

languagePragmas :: String -> [String]
languagePragmas source =
    sortOn id (concatMap pragmasFromLine (lines source))

pragmasFromLine :: String -> [String]
pragmasFromLine rawLine =
    case stripPrefix "{-# LANGUAGE" (trim rawLine) of
        Nothing -> []
        Just rest ->
            case breakOn "#-}" rest of
                Nothing -> []
                Just inside -> map trim (splitCommas inside)

splitCommas :: String -> [String]
splitCommas "" = []
splitCommas value =
    case break (== ',') value of
        (part, ',' : rest) -> part : splitCommas rest
        (part, _) -> [part]

breakOn :: String -> String -> Maybe String
breakOn needle haystack =
    search "" haystack
  where
    search _ "" = Nothing
    search prefix remaining
        | needle `isPrefixOf` remaining = Just (reverse prefix)
        | otherwise = search (head remaining : prefix) (tail remaining)

stripPrefix :: String -> String -> Maybe String
stripPrefix prefix value
    | prefix `isPrefixOf` value = Just (drop (length prefix) value)
    | otherwise = Nothing

compactWhitespace :: String -> String
compactWhitespace = unwords . words

trim :: String -> String
trim = trimRight . trimLeft

trimLeft :: String -> String
trimLeft = dropWhile isSpace

trimRight :: String -> String
trimRight = reverse . dropWhile isSpace . reverse
