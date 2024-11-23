import os
import pytest
from multilspy import SyncLanguageServer
from multilspy.multilspy_config import Language
from tests.test_utils import create_test_context
from pathlib import PurePath

def test_multilspy_go_sync_hover():
    """
    Test synchronous hover functionality with Go
    """
    code_language = Language.GO
    params = {
        "code_language": code_language,
        "repo_url": "https://github.com/gin-gonic/gin/",
        "repo_commit": "e46bd521859fdfc83c508f1d42c92cb7f91e9fcb"  # Using a stable release tag
    }
    
    with create_test_context(params) as context:
        print(f"Source directory: {context.source_directory}")
        lsp = SyncLanguageServer.create(context.config, context.logger, context.source_directory)
        print(f"LSP: {lsp.language_server.repository_root_path}")

        with lsp.start_server():
            path = str(PurePath("gin.go"))
            print(f"Testing with {path}")

            # Test hover
            result = lsp.request_hover(path, 69, 7)  # Engine struct definition
            print("****** Test hover ******")
            print(result)
            print("****** Test hover ******")
            assert result is not None
            assert "contents" in result

def test_multilspy_go_sync_definition():
    """
    Test synchronous go-to-definition functionality with Go
    """
    code_language = Language.GO
    params = {
        "code_language": code_language,
        "repo_url": "https://github.com/gin-gonic/gin/",
        "repo_commit": "e46bd521859fdfc83c508f1d42c92cb7f91e9fcb"
    }
    
    with create_test_context(params) as context:
        lsp = SyncLanguageServer.create(context.config, context.logger, context.source_directory)

        with lsp.start_server():
            path = str(PurePath("gin.go"))
            
            # Test go-to-definition
            result = lsp.request_definition(path, 69, 5)  # Engine struct definition
            assert isinstance(result, list)
            assert len(result) == 1

            item = result[0]
            assert item["relativePath"] == path
            assert "range" in item
            assert item["range"] == {
                "start": {"line": 69, "character": 5},
                "end": {"line": 69, "character": 14},
            }

def test_multilspy_go_sync_references():
    """
    Test synchronous find references functionality with Go
    """
    code_language = Language.GO
    params = {
        "code_language": code_language,
        "repo_url": "https://github.com/gin-gonic/gin/",
        "repo_commit": "e46bd521859fdfc83c508f1d42c92cb7f91e9fcb"
    }
    
    with create_test_context(params) as context:
        lsp = SyncLanguageServer.create(context.config, context.logger, context.source_directory)

        with lsp.start_server():
            path = str(PurePath("gin.go"))
            
            # Test find references
            result = lsp.request_references(path, 69, 5)  # Engine struct
            assert isinstance(result, list)
            assert len(result) > 0  # Engine should be referenced multiple times

            # Clean up URI and absolute path from results for consistent testing
            for item in result:
                if "uri" in item:
                    del item["uri"]
                if "absolutePath" in item:
                    del item["absolutePath"]
