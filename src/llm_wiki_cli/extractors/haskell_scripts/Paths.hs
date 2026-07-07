module Paths
    ( SourceFile (..)
    , collectSourceFiles
    , splitCommaList
    , toPosixPath
    ) where

import Control.Monad (forM)
import Data.Char (isSpace)
import Data.List (isPrefixOf, sortBy)
import Data.Ord (comparing)
import System.Directory
    ( canonicalizePath
    , doesDirectoryExist
    , doesFileExist
    , listDirectory
    )
import System.FilePath
    ( (</>)
    , isAbsolute
    , makeRelative
    , normalise
    , splitDirectories
    , takeExtension
    )

data SourceFile = SourceFile
    { sourceAbsolutePath :: FilePath
    , sourceRelativePath :: FilePath
    }
    deriving (Eq, Show)

collectSourceFiles :: FilePath -> Maybe String -> IO (Either String [SourceFile])
collectSourceFiles srcDir onlyFilesValue = do
    root <- canonicalizePath srcDir
    case onlyFilesValue of
        Just raw -> collectRequestedFiles root (splitCommaList raw)
        Nothing -> collectDiscoveredFiles root

collectRequestedFiles :: FilePath -> [FilePath] -> IO (Either String [SourceFile])
collectRequestedFiles root requested
    | null requested = pure (Left "--only-files must name at least one file")
    | otherwise = fmap sequenceSourceFiles (mapM (resolveRequestedFile root) requested)

resolveRequestedFile :: FilePath -> FilePath -> IO (Either String SourceFile)
resolveRequestedFile root requested = do
    let candidate =
            if isAbsolute requested
                then requested
                else root </> requested
    exists <- doesFileExist candidate
    if not exists
        then pure (Left ("requested file does not exist: " ++ requested))
        else do
            absolutePath <- canonicalizePath candidate
            pure (sourceFileFromAbsolute root requested absolutePath)

sourceFileFromAbsolute :: FilePath -> FilePath -> FilePath -> Either String SourceFile
sourceFileFromAbsolute root requested absolutePath =
    case safeRelative root absolutePath of
        Nothing -> Left ("requested file is outside --src-dir: " ++ requested)
        Just relativePath ->
            if isHaskellSource relativePath
                then
                    Right
                        SourceFile
                            { sourceAbsolutePath = absolutePath
                            , sourceRelativePath = toPosixPath relativePath
                            }
                else Left ("requested file is not a Haskell source: " ++ requested)

collectDiscoveredFiles :: FilePath -> IO (Either String [SourceFile])
collectDiscoveredFiles root = do
    paths <- listHaskellFiles root
    pure (Right (sortOnRelative paths))

listHaskellFiles :: FilePath -> IO [SourceFile]
listHaskellFiles root = do
    entries <- walk root
    pure (sortOnRelative entries)
  where
    walk dir = do
        names <- listDirectory dir
        fmap concat $
            forM names $ \name -> do
                let path = dir </> name
                isDir <- doesDirectoryExist path
                isFile <- doesFileExist path
                if isDir
                    then
                        if shouldSkipDirectory name
                            then pure []
                            else walk path
                    else
                        if isFile && isHaskellSource path
                            then do
                                absolutePath <- canonicalizePath path
                                pure
                                    [ SourceFile
                                        { sourceAbsolutePath = absolutePath
                                        , sourceRelativePath =
                                            toPosixPath (makeRelative root absolutePath)
                                        }
                                    ]
                            else pure []

shouldSkipDirectory :: FilePath -> Bool
shouldSkipDirectory name =
    name `elem` [".git", ".venv", "node_modules", "dist", "build"]

isHaskellSource :: FilePath -> Bool
isHaskellSource path = takeExtension path `elem` [".hs", ".lhs"]

safeRelative :: FilePath -> FilePath -> Maybe FilePath
safeRelative root absolutePath =
    let relativePath = normalise (makeRelative root absolutePath)
        parts = splitDirectories relativePath
     in if null relativePath
            || isAbsolute relativePath
            || ".." `elem` parts
            || "../" `isPrefixOf` toPosixPath relativePath
            then Nothing
            else Just relativePath

sequenceSourceFiles :: [Either String SourceFile] -> Either String [SourceFile]
sequenceSourceFiles values =
    case [message | Left message <- values] of
        message : _ -> Left message
        [] -> Right (sortOnRelative [sourceFile | Right sourceFile <- values])

sortOnRelative :: [SourceFile] -> [SourceFile]
sortOnRelative = sortByRelative

sortByRelative :: [SourceFile] -> [SourceFile]
sortByRelative = sortBy (comparing sourceRelativePath)

splitCommaList :: String -> [String]
splitCommaList value =
    [trim part | part <- splitCommas value, not (null (trim part))]

splitCommas :: String -> [String]
splitCommas "" = [""]
splitCommas value =
    case break (== ',') value of
        (part, ',' : rest) -> part : splitCommas rest
        (part, _) -> [part]

trim :: String -> String
trim = dropWhileEnd isSpace . dropWhile isSpace

dropWhileEnd :: (a -> Bool) -> [a] -> [a]
dropWhileEnd predicate = reverse . dropWhile predicate . reverse

toPosixPath :: FilePath -> FilePath
toPosixPath = map normalizeSeparator

normalizeSeparator :: Char -> Char
normalizeSeparator '\\' = '/'
normalizeSeparator value = value
