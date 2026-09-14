{-# LANGUAGE ScopedTypeVariables #-}
{-# LANGUAGE RankNTypes #-}

-- A separate GHC parse-only observer; no target modules are loaded or evaluated.
module Main where

import Control.Monad (replicateM)
import Control.Monad.IO.Class (liftIO)
import Data.Char (ord)
import Data.Data (showConstr, toConstr)
import Data.List (intercalate, isPrefixOf)
import GHC (runGhc, getSessionDynFlags)
import GHC.Data.FastString (mkFastString)
import GHC.Data.StringBuffer (stringToStringBuffer)
import GHC.Driver.Config.Parser (initParserOpts)
import GHC.Driver.Session (parseDynamicFilePragma)
import GHC.Hs
import GHC.Parser (parseModule)
import GHC.Parser.Annotation (getLocA)
import GHC.Parser.Header (getOptions)
import GHC.Parser.Lexer (ParseResult (..), getPsErrorMessages, initParserState, unP)
import GHC.Types.Error (NoDiagnosticOpts (..))
import GHC.Utils.Error (pprMessages)
import GHC.Types.Name.Reader (RdrName, rdrNameOcc)
import GHC.Types.Name.Occurrence (occNameString)
import GHC.Types.SrcLoc
import GHC.Unit.Module (moduleNameString)
import GHC.Utils.Outputable (Outputable, ppr, showSDocUnsafe)
import Numeric (showHex)
import System.Environment (getArgs)
import System.IO (stdin, stdout, utf8, hSetEncoding)

data J = S String | N Int | A [J] | O [(String,J)]
render :: J -> String
render (S x) = '"' : concatMap escape x ++ "\""
  where
    escape '"' = "\\\""
    escape '\\' = "\\\\"
    escape c | ord c < 32 = let hex=showHex (ord c) "" in "\\u" ++ replicate (4-length hex) '0' ++ hex
    escape c = [c]
render (N x) = show x
render (A xs) = "[" ++ intercalate "," (map render xs) ++ "]"
render (O xs) = "{" ++ intercalate "," [render (S k) ++ ":" ++ render v | (k,v)<-xs] ++ "}"

readText :: IO String
readText = do
    count <- readLn
    text <- replicateM count getChar
    separator <- getChar
    if separator == '\n' then pure text else fail "invalid request framing"

typeShape :: LHsType GhcPs -> J
typeShape located = case unLoc located of
    HsParTy _ inner -> typeShape inner
    HsTyVar _ promotion identifier -> tagged "variable" [S (showConstr (toConstr promotion)), S (pretty (unLoc identifier))]
    HsFunTy _ arrow left right -> tagged "arrow" [arrowShape arrow, typeShape left, typeShape right]
    HsAppTy _ left right -> tagged "application" [typeShape left,typeShape right]
    HsAppKindTy _ left right -> tagged "kind-application" [typeShape left,typeShape right]
    HsQualTy _ context body -> tagged "qualified" [A (map typeShape (unLoc context)), typeShape body]
    HsForAllTy _ telescope body -> tagged "forall" [S (pretty telescope),typeShape body]
    HsListTy _ item -> tagged "list" [typeShape item]
    HsTupleTy _ sortValue items -> tagged "tuple" [S (showConstr (toConstr sortValue)),A (map typeShape items)]
    HsSumTy _ items -> tagged "sum" (map typeShape items)
    HsOpTy _ promotion left operator right -> tagged "operator" [S (showConstr (toConstr promotion)),typeShape left,S (pretty (unLoc operator)),typeShape right]
    HsKindSig _ body kind -> tagged "kind" [typeShape body,typeShape kind]
    HsTyLit _ literal -> tagged "literal" [S (pretty literal)]
    HsStarTy _ _ -> tagged "star" []
    HsWildCardTy _ -> tagged "wildcard" []
    HsExplicitListTy _ promotion items -> tagged "promoted-list" [S (showConstr (toConstr promotion)),A (map typeShape items)]
    HsExplicitTupleTy _ items -> tagged "promoted-tuple" (map typeShape items)
    HsDocTy _ body _ -> typeShape body
    other -> error ("Unsupported oracle type node: " ++ pretty other)
  where
    tagged tag fields = A (S tag : fields)
    arrowShape (HsUnrestrictedArrow _) = S "unrestricted"
    arrowShape (HsLinearArrow _) = S "linear"
    arrowShape (HsExplicitMult _ multiplicity _) = tagged "multiplicity" [typeShape multiplicity]

pretty :: Outputable a => a -> String
pretty = showSDocUnsafe . ppr
name :: RdrName -> String
name = occNameString . rdrNameOcc
line :: SrcSpan -> Int
line (RealSrcSpan spanValue _) = srcSpanStartLine spanValue
line _ = 0

parse :: String -> String -> String -> IO (HsModule GhcPs)
parse libdir filename text = runGhc (Just libdir) $ do
    flags <- getSessionDynFlags
    let buffer = stringToStringBuffer text
        (_,options) = getOptions (initParserOpts flags) buffer filename
        syntax = filter (isPrefixOf "-X" . unLoc) options
    (effective,_,_) <- parseDynamicFilePragma flags syntax
    let state = initParserState (initParserOpts effective) buffer (mkRealSrcLoc (mkFastString filename) 1 1)
    case unP parseModule state of
      POk _ parsed -> pure (unLoc parsed)
      PFailed failed -> liftIO (fail ("GHC parse failed: " ++ pretty (pprMessages NoDiagnosticOpts (getPsErrorMessages failed))))

record :: String -> String -> Int -> [(String,J)] -> J
record kind symbol position more = O ([ ("kind",S kind), ("name",S symbol), ("owner",S ""), ("line",N position)] ++ more)

decl :: LHsDecl GhcPs -> [J]
decl located = case unLoc located of
    SigD _ (TypeSig _ names (HsWC _ signature)) ->
      case unLoc signature of
        HsSig _ _ body -> [record "function" (name (unLoc n)) position [("declaration_kind",S "signature"),("signature",S (pretty body))] | n<-names]
        _ -> []
    ValD _ FunBind {fun_id=identifier} -> [record "function" (name (unLoc identifier)) position [("declaration_kind",S "function")]]
    ValD _ PatBind {pat_lhs=patternValue} -> case unLoc patternValue of
      VarPat _ identifier -> [record "function" (name (unLoc identifier)) position [("declaration_kind",S "value")]]
      _ -> []
    TyClD _ declaration -> case declaration of
      SynDecl {tcdLName=identifier,tcdRhs=body} -> [record "class" (name (unLoc identifier)) position [("declaration_kind",S "type"),("type",S (pretty body))]]
      DataDecl {tcdLName=identifier} -> [record "class" (name (unLoc identifier)) position [("declaration_kind",S "data")]]
      ClassDecl {tcdLName=identifier} -> [record "class" (name (unLoc identifier)) position [("declaration_kind",S "class")]]
      _ -> []
    _ -> []
  where position = line (getLocA located)

run :: String -> (String,String,String) -> IO J
run libdir (mode,text,filename)
    | mode == "source" = do
        parsed <- parse libdir filename text
        let imports = [O [("module",S (moduleNameString (unLoc (ideclName (unLoc item))))),("line",N (line (getLocA item)))] | item<-hsmodImports parsed]
        pure (O [("declarations",A (concatMap decl (hsmodDecls parsed))),("imports",A imports),("module",S (maybe "Main" (moduleNameString . unLoc) (hsmodName parsed)))])
    | mode == "type" = do
        parsed <- parse libdir "Probe.hs" (pragmas ++ "\nmodule Probe where\ntype Probe =\n" ++ unlines ["    " ++ part | part <- lines text])
        case [body | L _ (TyClD _ SynDecl {tcdRhs=body}) <- hsmodDecls parsed] of
          [body] -> pure (typeShape body)
          _ -> fail "expected one type"
    | otherwise = fail "Haskell expression normalization is not declared by this audit"
  where pragmas = "{-# LANGUAGE ExplicitForAll, RankNTypes, DataKinds, TypeOperators, KindSignatures, PolyKinds, ConstraintKinds, MagicHash, UnboxedTuples, LinearTypes #-}"

main :: IO ()
main = do
    hSetEncoding stdin utf8
    hSetEncoding stdout utf8
    [libdir] <- getArgs
    count <- readLn
    jobs <- replicateM count ((,,) <$> readText <*> readText <*> readText)
    results <- mapM (run libdir) jobs
    putStrLn (render (A results))
