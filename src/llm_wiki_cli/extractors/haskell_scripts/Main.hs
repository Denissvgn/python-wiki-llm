module Main
    ( main
    ) where

import Control.Monad (forM)
import Data.List (intercalate)
import System.Environment (getArgs)
import System.Exit (exitFailure)
import System.IO (hPutStrLn, stderr)

import Json (renderInventoryJson)
import Parser (parseSourceFile)
import Paths (SourceFile (..), collectSourceFiles)

data Args = Args
    { argsSrcDir :: Maybe FilePath
    , argsOnlyFiles :: Maybe String
    , argsDeep :: Bool
    }
    deriving (Eq, Show)

emptyArgs :: Args
emptyArgs = Args {argsSrcDir = Nothing, argsOnlyFiles = Nothing, argsDeep = False}

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
            sourceFilesResult <- collectSourceFiles srcDir (argsOnlyFiles args)
            case sourceFilesResult of
                Left message -> failWith message
                Right sourceFiles -> do
                    parsed <- forM sourceFiles parseOne
                    case [message | Left message <- parsed] of
                        [] -> putStrLn (renderInventoryJson (rights parsed))
                        messages -> failWith (intercalate "\n" messages)
  where
    parseOne sourceFile = do
        result <-
            parseSourceFile
                (sourceAbsolutePath sourceFile)
                (sourceRelativePath sourceFile)
        pure ((,) (sourceRelativePath sourceFile) <$> result)

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
    parse args ("--deep" : rest) = parse args {argsDeep = True} rest
    parse _ (unknown : _) = Left ("unknown argument: " ++ unknown)

validateArgs :: Args -> Either String Args
validateArgs args =
    case argsSrcDir args of
        Nothing -> Left "--src-dir is required"
        Just "" -> Left "--src-dir requires a path"
        Just _ -> Right args

rights :: [Either left value] -> [value]
rights values = [value | Right value <- values]

failWith :: String -> IO a
failWith message = do
    hPutStrLn stderr message
    exitFailure
