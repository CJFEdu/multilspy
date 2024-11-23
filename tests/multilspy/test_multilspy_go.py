"""
This file contains tests for running the Go Language Server: gopls
"""

import os
from pathlib import PurePath
from multilspy.language_server import LanguageServer
from multilspy.multilspy_config import Language
from multilspy.multilspy_types import Position, CompletionItemKind
from tests.test_utils import create_test_context
import pytest
import sys
import asyncio
from test_config import setup_test_params

pytest_plugins = ("pytest_asyncio",)




@pytest.mark.asyncio
async def test_multilspy_go_definition():
    """
    Test go-to-definition functionality with Go
    """
    params = setup_test_params(Language.GO)
    
    with create_test_context(params) as context:
        context.source_directory = os.path.join(context.source_directory, context.config.code_language.value)
        lsp = LanguageServer.create(context.config, context.logger, context.source_directory)
        
        async with lsp.start_server():
            path = str(PurePath("main.go"))
            
            # Test go-to-definition
            result = await lsp.request_definition(path, 65, 15)  
            assert isinstance(result, list)
            assert len(result) == 1

            item = result[0]
            assert item["relativePath"] == str(PurePath("quotes.go"))
            assert item["range"] == {
                "start": {"line": 16, "character": 5},
                "end": {"line": 16, "character": 14},
            }

@pytest.mark.asyncio
async def test_multilspy_go_references():
    """
    Test find references functionality with Go
    """
    params = setup_test_params(Language.GO)
    
    with create_test_context(params) as context:
        context.source_directory = os.path.join(context.source_directory, context.config.code_language.value)
        lsp = LanguageServer.create(context.config, context.logger, context.source_directory)
        
        async with lsp.start_server():
            path = str(PurePath("main.go"))
            
            # Test find references
            result = await lsp.request_references(path, 65, 5)
            assert isinstance(result, list)
            assert len(result) > 0  # Engine should be referenced multiple times

            # Clean up URI and absolute path from results for consistent testing
            for item in result:
                del item["uri"]
                del item["absolutePath"]

            assert result == [
                {
                    'range': {
                        'start': {'line': 85, 'character': 15}, 
                        'end': {'line': 85, 'character': 21}
                        },
                    'relativePath': 'main.go'
                },
                {
                    'range': {
                        'start': {'line': 87, 'character': 15}, 
                        'end': {'line': 87, 'character': 21}
                        },
                    'relativePath': 'main.go'
                },
                {
                    'range': {
                        'start': {'line': 89, 'character': 15}, 
                        'end': {'line': 89, 'character': 21}
                        },
                    'relativePath': 'main.go'
                }
            ]

@pytest.mark.asyncio
async def test_multilspy_go_delete():
    """
    Test delete functionality with Go
    """
    params = setup_test_params(Language.GO)
    
    with create_test_context(params) as context:
        context.source_directory = os.path.join(context.source_directory, context.config.code_language.value)
        lsp = LanguageServer.create(context.config, context.logger, context.source_directory)
        
        async with lsp.start_server():
            path = str(PurePath("main.go"))
            with lsp.open_file(path):
                deleted_text = lsp.delete_text_between_positions(
                        path,
                        Position(line=89, character=22),
                        Position(line=89, character=38)
                    )
                assert deleted_text == "GetWisdomQuote()"


@pytest.mark.asyncio
async def test_multilspy_go_hover():
    """
    Test hover functionality with Go
    """
    params = setup_test_params(Language.GO)
    
    with create_test_context(params) as context:
        context.source_directory = os.path.join(context.source_directory, context.config.code_language.value)
        lsp = LanguageServer.create(context.config, context.logger, context.source_directory)
        
        async with lsp.start_server():
            path = str(PurePath("main.go"))
            with lsp.open_file(path):
                deleted_text = lsp.delete_text_between_positions(
                        path,
                        Position(line=89, character=22),
                        Position(line=89, character=38)
                    )
                assert deleted_text == "GetWisdomQuote()"

                lsp.insert_text_at_position(path, 89, 22, "GetHumorQuote()")

                result = await lsp.request_hover(path, 89, 22)
                assert result == {
                    'contents': {
                        'kind': 'markdown',
                        'value': '```go\nfunc (q *Quoter) GetHumorQuote() string\n```\n\n[`(main.Quoter).GetHumorQuote` on pkg.go.dev](https://pkg.go.dev/quiz#Quoter.GetHumorQuote)'
                    },
                    'range': {
                        'start': {'line': 89, 'character': 22},
                        'end': {'line': 89, 'character': 35}
                    }
                }

@pytest.mark.asyncio
async def test_multilspy_go_completion():
    """
    Test completion functionality with Go
    """
    params = setup_test_params(Language.GO)
    
    with create_test_context(params) as context:
        context.source_directory = os.path.join(context.source_directory, context.config.code_language.value)
        lsp = LanguageServer.create(context.config, context.logger, context.source_directory)
        
        async with lsp.start_server():
            path = str(PurePath("main.go"))
            with lsp.open_file(path):
                deleted_text = lsp.delete_text_between_positions(
                        path,
                        Position(line=89, character=8),
                        Position(line=89, character=39)
                    )
                assert deleted_text == "rintln(quoter.GetWisdomQuote())"
                result = await lsp.request_completions(path, 89, 8, allow_incomplete=True)
                assert isinstance(result, list)
                assert len(result) > 0

                dict_result = {}
                for item in result:
                    dict_result[item["completionText"]] = item

                assert dict_result == {
                    "Println": {'completionText': 'Println', 'detail': 'func(a ...any) (n int, err error)', 'kind': 3},
                    "Print": {'completionText': 'Print', 'detail': 'func(a ...any) (n int, err error)', 'kind': 3},
                    "Printf": {'completionText': 'Printf', 'detail': 'func(format string, a ...any) (n int, err error)', 'kind': 3}
                }

@pytest.mark.asyncio
async def test_multilspy_go_document_symbols():
    """
    Test document symbols functionality with Go
    """
    params = setup_test_params(Language.GO)
    
    with create_test_context(params) as context:
        context.source_directory = os.path.join(context.source_directory, context.config.code_language.value)
        lsp = LanguageServer.create(context.config, context.logger, context.source_directory)
        
        async with lsp.start_server():
            path = str(PurePath("quiz.go"))
            result = await lsp.request_document_symbols(path)
            assert isinstance(result[0], list)
            assert len(result[0]) > 0

            for item in result[0]:
                item['location']["uri"] = os.path.basename(item['location']["uri"].replace("file://", ""))

            assert result[0] == [
                {'location': {'uri': 'quiz.go', 'range': {'start': {'line': 9, 'character': 5}, 'end': {'line': 15, 'character': 1}}}, 'name': 'Quiz', 'kind': 23},
                {'location': {'uri': 'quiz.go', 'range': {'start': {'line': 17, 'character': 0}, 'end': {'line': 37, 'character': 1}}}, 'name': '(*Quiz).selectQuestions', 'kind': 6},
                {'location': {'uri': 'quiz.go', 'range': {'start': {'line': 39, 'character': 0}, 'end': {'line': 86, 'character': 1}}}, 'name': '(*Quiz).askQuestion', 'kind': 6},
                {'location': {'uri': 'quiz.go', 'range': {'start': {'line': 88, 'character': 0}, 'end': {'line': 134, 'character': 1}}}, 'name': '(*Quiz).run', 'kind': 6}
            ]

