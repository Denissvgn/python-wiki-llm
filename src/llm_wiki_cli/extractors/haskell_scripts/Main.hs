module Main
    ( main
    ) where

import Control.Exception (IOException, try)
import Control.Monad (forM)
import Data.List (intercalate)
import System.Environment (getArgs)
import System.Exit (exitFailure)
import System.IO (hPutStrLn, stderr)

import Inventory (FileEntry)
import Json (renderInventoryJson, renderDiagnosticsJson)
import Parser (parseSourceFile)
import Paths (SourceFile (..), collectSourceFiles, collectDiagnosticSourceFiles)

data Args = Args
    { argsSrcDir :: Maybe FilePath
    , argsOnlyFiles :: Maybe String
    , argsDeep :: Bool
    , argsDiagnostics :: Bool
    , argsFiles :: [FilePath]
    }
    deriving (Eq, Show)

emptyArgs :: Args
emptyArgs = Args {argsSrcDir = Nothing, argsOnlyFiles = Nothing, argsDeep = False, argsDiagnostics = False, argsFiles = []}

main :: IO ()
main = do
    parsedArgs <- parseArgs <$> getArgs
    case parsedArgs >>= validateArgs of
        Left message -> failWith message
        Right args -> run args

run :: Args -> IO ()
run args =
    case argsSrcDir args of
        Nothing -> failWith "--src-dir is required"
        Just srcDir -> do
            sourceFilesResult <-
                if argsDiagnostics args && not (null (argsFiles args))
                    then collectDiagnosticSourceFiles srcDir (argsFiles args)
                    else collectSourceFiles srcDir (argsOnlyFiles args)
            case sourceFilesResult of
                Left message -> failWith message
                Right sourceFiles -> do
                    parsed <- forM sourceFiles (if argsDiagnostics args then parseDiagnostic else parseOne)
                    if argsDiagnostics args
                        then putStrLn (renderDiagnosticsJson (rights parsed) [value | Left value <- parsed])
                        else case [message | Left (_, _, message) <- parsed] of
                            [] -> putStrLn (renderInventoryJson (rights parsed))
                            messages -> failWith (intercalate "\n" messages)
  where
    parseOne sourceFile = do
        result <-
            parseSourceFile
                (sourceAbsolutePath sourceFile)
                (sourceRelativePath sourceFile)
        pure $ case result of
            Right entry -> Right (sourceRelativePath sourceFile, entry)
            Left message -> Left (sourceRelativePath sourceFile, "syntax-error", message)
    parseDiagnostic sourceFile = do
        result <- try (parseSourceFile (sourceAbsolutePath sourceFile) (sourceRelativePath sourceFile)) :: IO (Either IOException (Either String FileEntry))
        pure $ case result of
            Left problem -> Left (sourceRelativePath sourceFile, "read-error", show problem)
            Right (Left message) -> Left (sourceRelativePath sourceFile, "syntax-error", message)
            Right (Right entry) -> Right (sourceRelativePath sourceFile, entry)

parseArgs :: [String] -> Either String Args
parseArgs = parse emptyArgs
  where
    parse args [] = Right args
    parse args ("--src-dir" : value : rest) =
        parse args {argsSrcDir = Just value} rest
    parse _ ["--src-dir"] = Left "--src-dir requires a path"
    parse args ("--only-files" : value : rest) =
        parse args {argsOnlyFiles = Just value} rest
    parse _ ["--only-files"] = Left "--only-files requires a value"
    parse args ("--diagnostics-v1" : rest) = parse args {argsDiagnostics = True} rest
    parse args ("--file-v1" : value : rest) = parse args {argsFiles = argsFiles args ++ [value]} rest
    parse _ ["--file-v1"] = Left "--file-v1 requires a path"
    parse args ("--deep" : rest) = parse args {argsDeep = True} rest
    parse _ (unknown : _) = Left ("unknown argument: " ++ unknown)

validateArgs :: Args -> Either String Args
validateArgs args
    | not (null (argsFiles args)) && not (argsDiagnostics args) = Left "--file-v1 requires --diagnostics-v1"
    | otherwise = case argsSrcDir args of
        Nothing -> Left "--src-dir is required"
        Just "" -> Left "--src-dir requires a path"
        Just _ -> Right args

rights :: [Either left value] -> [value]
rights values = [value | Right value <- values]

failWith :: String -> IO a
failWith message = do
    hPutStrLn stderr message
    exitFailure
