"""
This file contains tests for running the Go Language Server: gopls
"""

import os
import json
from pathlib import PurePath
from multilspy.language_server import LanguageServer
from multilspy.multilspy_config import Language
from multilspy.multilspy_types import Position, CompletionItemKind
from tests.test_utils import create_test_context
import pytest
import sys
import asyncio
from test_config import setup_test_params
from expected_results.go.code_locations import get_code_locations

pytest_plugins = ("pytest_asyncio",)



async def start_server():
    """
    Start the language server
    """
    params = setup_test_params(Language.GO)
    code_locations = get_code_locations()
    
    with create_test_context(params) as context:
        context.source_directory = os.path.join(context.source_directory, context.config.code_language.value)
        lsp = LanguageServer.create(context.config, context.logger, context.source_directory)
        
        async with lsp.start_server():
            yield lsp

# @pytest.mark.asyncio
# async def test_multilspy_go_declaration():
#     """
#     Test go-to-declaration functionality with Go
#     """
#     code_locations = get_code_locations()
#     async for lsp in start_server():
#         path = str(PurePath(code_locations["definition"]["path"]))
        
#         # Test go-to-declaration
#         result = await lsp.request_declaration(path, 
#             code_locations["definition"]["line"], 
#             code_locations["definition"]["character"]
#         )  
#         assert isinstance(result, list)
#         assert len(result) == 1

@pytest.mark.asyncio
async def test_multilspy_go_definition():
    """
    Test go-to-definition functionality with Go
    """
    code_locations = get_code_locations()
    async for lsp in start_server():
        path = str(PurePath(code_locations["definition"]["path"]))
        
        # Test go-to-definition
        result = await lsp.request_definition(path, 
            code_locations["definition"]["line"], 
            code_locations["definition"]["character"]
        )  
        assert isinstance(result, list)
        assert len(result) == 1

        # Load expected results
        expected_results_file = os.path.join(os.path.dirname(__file__), 'expected_results', 'go', 'result_definition.json')
        with open(expected_results_file, 'r') as f:
            expected_results = json.load(f)

        # Clean up actual results for comparison
        for item in result:
            item["uri"] = os.path.basename(item["uri"].replace("file://", ""))
            del item["absolutePath"]

        assert result == expected_results


@pytest.mark.asyncio
async def test_multilspy_go_references():
    """
    Test find references functionality with Go
    """
    code_locations = get_code_locations()
    async for lsp in start_server():
        path = str(PurePath(code_locations["references"]["path"]))
        
        # Test find references
        result = await lsp.request_references(path, 
            code_locations["references"]["line"], 
            code_locations["references"]["character"]
        )  
        assert isinstance(result, list)
        assert len(result) > 0

        # Load expected results
        expected_results_file = os.path.join(os.path.dirname(__file__), 'expected_results', 'go', 'result_references.json')
        with open(expected_results_file, 'r') as f:
            expected_results = json.load(f)

        # Clean up actual results for comparison
        for item in result:
            item["uri"] = os.path.basename(item["uri"].replace("file://", ""))
            del item["absolutePath"]

        assert result == expected_results
            

@pytest.mark.asyncio
async def test_multilspy_go_delete():
    """
    Test delete functionality with Go
    """
    code_locations = get_code_locations()
    async for lsp in start_server():
        path = str(PurePath(code_locations["definition"]["path"]))
        with lsp.open_file(path):
            deleted_text = lsp.delete_text_between_positions(
                    path,
                    Position(line=code_locations["definition"]["line"], character=code_locations["definition"]["character"]),
                    Position(line=code_locations["definition"]["line"], character=code_locations["definition"]["character"] + len(code_locations["delete"]["text"]))
                )
            assert deleted_text == code_locations["delete"]["text"]

@pytest.mark.asyncio
async def test_multilspy_go_insert_text():
    """
    Test insert text functionality with Go
    """
    code_locations = get_code_locations()
    async for lsp in start_server():
        path = str(PurePath(code_locations["definition"]["path"]))
        with lsp.open_file(path):
            deleted_text = lsp.delete_text_between_positions(
                    path,
                    Position(line=code_locations["definition"]["line"], character=code_locations["definition"]["character"]),
                    Position(line=code_locations["definition"]["line"], character=code_locations["definition"]["character"] + len(code_locations["delete"]["text"]))
                )
            assert deleted_text == code_locations["delete"]["text"]

            position =lsp.insert_text_at_position(path, 
                line=code_locations["definition"]["line"], 
                column=code_locations["definition"]["character"], 
                text_to_be_inserted=code_locations["delete"]["text"])

            assert position == Position(line=code_locations["definition"]["line"], 
                character=code_locations["definition"]["character"]+len(code_locations["delete"]["text"])
            )
                

@pytest.mark.asyncio
async def test_multilspy_go_hover():
    """
    Test hover functionality with Go
    """
    code_locations = get_code_locations()
    async for lsp in start_server():
        path = str(PurePath(code_locations["definition"]["path"]))
        with lsp.open_file(path):
            # Test hover
            result = await lsp.request_hover(path, 
                code_locations["definition"]["line"], 
                code_locations["definition"]["character"]
            )
            assert result is not None
            # Load expected results
            expected_results_file = os.path.join(os.path.dirname(__file__), 'expected_results', 'go', 'result_hover.json')
            with open(expected_results_file, 'r') as f:
                expected_results = json.load(f)
                assert result == expected_results

@pytest.mark.asyncio
async def test_multilspy_go_completion():
    """
    Test completion functionality with Go
    """
    code_locations = get_code_locations()
    async for lsp in start_server():
        path = str(PurePath(code_locations["definition"]["path"]))

        with lsp.open_file(path):
            deleted_text = lsp.delete_text_between_positions(
                    path,
                    Position(line=code_locations["definition"]["line"], character=code_locations["definition"]["character"]),
                    Position(line=code_locations["definition"]["line"], character=code_locations["definition"]["character"] + len(code_locations["delete"]["text"]))
                )

        # Test completion
        result = await lsp.request_completions(path, 
            code_locations["definition"]["line"], 
            code_locations["definition"]["character"],
            allow_incomplete=True
        )

        # Load expected results
        expected_results_file = os.path.join(os.path.dirname(__file__), 'expected_results', 'go', 'result_completion.json')
        with open(expected_results_file, 'r') as f:
            expected_results = json.load(f)

        for item in result:
            assert item in expected_results


@pytest.mark.asyncio
async def test_multilspy_go_document_symbols():
    """
    Test document symbols functionality with Go
    """
    code_locations = get_code_locations()
    async for lsp in start_server():
        path = str(PurePath(code_locations["references"]["path"]))
        result = await lsp.request_document_symbols(path)
        assert isinstance(result[0], list)
        assert len(result[0]) > 0

        # Load expected results
        expected_results_file = os.path.join(os.path.dirname(__file__), 'expected_results', 'go', 'result_document_symbols.json')
        with open(expected_results_file, 'r') as f:
            expected_results = json.load(f)

        for item in result[0]:
            item['location']["uri"] = os.path.basename(item['location']["uri"].replace("file://", ""))
            assert item in expected_results[0]

        

@pytest.mark.asyncio
async def test_multilspy_go_save_document():
    """
    Test save document functionality with Go
    """
    code_locations = get_code_locations()
    async for lsp in start_server():
        path = str(PurePath(code_locations["save_document"]["path"]))


        quotes_path = os.path.join(lsp.repository_root_path, code_locations["save_document"]["path"])

        with lsp.open_file(path):
            
            # Add new function to the end of quotes.go
            with open(quotes_path, 'a') as f:
                f.write(code_locations["save_document"]["text"])
                
            lsp.insert_text_at_position(path,
                code_locations["save_document"]["line"],
                code_locations["save_document"]["character"],
                code_locations["save_document"]["text"]
            )

            result = await lsp.request_document_symbols(path)
            assert isinstance(result[0], list)
            assert len(result[0]) > 0

            # Load expected results
            expected_results_file = os.path.join(os.path.dirname(__file__), 'expected_results', 'go', 'result_save_document.json')
            with open(expected_results_file, 'r') as f:
                expected_results = json.load(f)

            for item in result[0]:
                item['location']["uri"] = os.path.basename(item['location']["uri"].replace("file://", ""))
                assert item in expected_results[0]

            lsp.save_file(path)

@pytest.mark.asyncio
async def test_multilspy_go_request_implementation():
    """
    Test request implementation functionality with Go
    """
    code_locations = get_code_locations()
    async for lsp in start_server():
        path = str(PurePath(code_locations["implementation"]["path"]))
        
        # Test request implementation
        result = await lsp.request_implementation(path, 
            code_locations["implementation"]["line"],
            code_locations["implementation"]["character"]
        )
        assert isinstance(result, list)
        assert len(result) > 0

        # Load expected results
        expected_results_file = os.path.join(os.path.dirname(__file__), 'expected_results', 'go', 'result_implementation.json')
        with open(expected_results_file, 'r') as f:
            expected_results = json.load(f)

        # Clean up actual results for comparison
        for item in result:
            item["uri"] = os.path.basename(item["uri"].replace("file://", ""))
            assert item in expected_results
