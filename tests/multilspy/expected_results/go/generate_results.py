"""
This script generates expected results for LSP functionality tests
"""

import os
import json
from pathlib import PurePath
from multilspy.language_server import LanguageServer
from multilspy.multilspy_config import Language
from multilspy.multilspy_types import Position, CompletionItemKind
import pytest
import sys
import asyncio

# Add parent directory to sys.path
for n in range(1, 5):
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '/'.join(['..'] * (n))))
    sys.path.insert(0, parent_dir)

from test_config import setup_test_params
from tests.test_utils import create_test_context
from code_locations import get_code_locations


async def start_server():
    """
    Start the language server
    """
    params = setup_test_params(Language.GO)
    
    with create_test_context(params) as context:
        context.source_directory = os.path.join(context.source_directory, context.config.code_language.value)
        lsp = LanguageServer.create(context.config, context.logger, context.source_directory)
        
        async with lsp.start_server():
            await generate_results_declaration(lsp)
            await generate_results_definition(lsp)
            await generate_results_references(lsp)
            await generate_results_hover(lsp)
            await generate_results_completion(lsp)
            await generate_results_document_symbols(lsp)
            await generate_results_save_document(lsp)
            await generate_results_implementation(lsp)

async def generate_results_declaration(lsp):
    """
    Test go-to-declaration functionality with Go
    """
    code_locations = get_code_locations()
    path = str(PurePath(code_locations["definition"]["path"]))
    
    # Test go-to-declaration
    result = await lsp.request_declaration(path, 
        code_locations["definition"]["line"], 
        code_locations["definition"]["character"]
    )  
    
    # Save results to JSON file
    # result_file = os.path.join(os.path.dirname(__file__), 'result_declaration.json')
    # for item in result:
    #     item["uri"] = os.path.basename(item["uri"].replace("file://", ""))
    with open(result_file, 'w') as f:
        json.dump(result, f, indent=2)

async def generate_results_definition(lsp):
    """
    Test go-to-definition functionality with Go
    """
    code_locations = get_code_locations()
    path = str(PurePath(code_locations["definition"]["path"]))
    result = await lsp.request_definition(path, 
        code_locations["definition"]["line"], 
        code_locations["definition"]["character"]
    )

    for item in result:
        item["uri"] = os.path.basename(item["uri"].replace("file://", ""))
        del item["absolutePath"]

    # Save results to JSON file
    result_file = os.path.join(os.path.dirname(__file__), 'result_definition.json')
    with open(result_file, 'w') as f:
        json.dump(result, f, indent=2)

async def generate_results_references(lsp):
    """
    Test find references functionality with Go
    """
    code_locations = get_code_locations()
    path = str(PurePath(code_locations["references"]["path"]))
    result = await lsp.request_references(path, 
        code_locations["references"]["line"], 
        code_locations["references"]["character"]
    )

    for item in result:
        item["uri"] = os.path.basename(item["uri"].replace("file://", ""))
        del item["absolutePath"]

    # Save results to JSON file
    result_file = os.path.join(os.path.dirname(__file__), 'result_references.json')
    with open(result_file, 'w') as f:
        json.dump(result, f, indent=2)

async def generate_results_hover(lsp):
    """
    Test hover functionality with Go
    """
    code_locations = get_code_locations()
    path = str(PurePath(code_locations["definition"]["path"]))
    result = await lsp.request_hover(path, 
        code_locations["definition"]["line"], 
        code_locations["definition"]["character"]
    )

    # Save results to JSON file
    result_file = os.path.join(os.path.dirname(__file__), 'result_hover.json')
    with open(result_file, 'w') as f:
        json.dump(result, f, indent=2)

async def generate_results_completion(lsp):
    """
    Test completion functionality with Go
    """
    code_locations = get_code_locations()
    path = str(PurePath(code_locations["definition"]["path"]))
    with lsp.open_file(path):
        deleted_text = lsp.delete_text_between_positions(
                path,
                Position(line=code_locations["definition"]["line"], character=code_locations["definition"]["character"]),
                Position(line=code_locations["definition"]["line"], character=code_locations["definition"]["character"] + len(code_locations["delete"]["text"]))
            )

    result = await lsp.request_completions(path, 
        code_locations["definition"]["line"], 
        code_locations["definition"]["character"],
        allow_incomplete=True
    )

    # Save results to JSON file
    result_file = os.path.join(os.path.dirname(__file__), 'result_completion.json')
    with open(result_file, 'w') as f:
        json.dump(result, f, indent=2)

async def generate_results_document_symbols(lsp):
    """
    Test document symbols functionality with Go
    """
    code_locations = get_code_locations()
    path = str(PurePath(code_locations["references"]["path"]))
    result = await lsp.request_document_symbols(path)

    # Save results to JSON file
    result_file = os.path.join(os.path.dirname(__file__), 'result_document_symbols.json')
    for item in result[0]:
        item['location']["uri"] = os.path.basename(item['location']["uri"].replace("file://", ""))
    with open(result_file, 'w') as f:
        json.dump(result, f, indent=2)

async def generate_results_save_document(lsp):
    """
    Test save document functionality with Go
    """
    code_locations = get_code_locations()
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

        # Save results to JSON file
        result_file = os.path.join(os.path.dirname(__file__), 'result_save_document.json')
        for item in result[0]:
            item['location']["uri"] = os.path.basename(item['location']["uri"].replace("file://", ""))
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)

async def generate_results_implementation(lsp):
    """
    Test request implementation functionality with Go
    """
    code_locations = get_code_locations()
    path = str(PurePath(code_locations["implementation"]["path"]))
    result = await lsp.request_implementation(path, 
        code_locations["implementation"]["line"],
        code_locations["implementation"]["character"]
    )

    # Save results to JSON file
    result_file = os.path.join(os.path.dirname(__file__), 'result_implementation.json')
    for item in result:
        item["uri"] = os.path.basename(item["uri"].replace("file://", ""))
    with open(result_file, 'w') as f:
        json.dump(result, f, indent=2)

def main():
    """
    Main entry point for generating test results
    """
    # Create results directory if it doesn't exist
    results_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(results_dir, exist_ok=True)

    print("Generating test results...")
    
    # Run the async function
    asyncio.run(start_server())
    
    print("Results generation complete!")

if __name__ == "__main__":
    main()
