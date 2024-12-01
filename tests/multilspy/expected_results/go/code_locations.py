import os

def get_code_locations() -> dict:
    """
    Get code locations for language server tests
    
    Returns:
        Dictionary containing code locations
    """
    return {
        "definition": {
            "path": "main.go",
            "line": 22,
            "character": 14
        },
        "references": {
            "path": os.path.join( "quiz_logic","quotes.go"),
            "line": 10,
            "character": 6
        },
        "delete": {
            "text": "howMenu()"
        },
        "save_document": {
            "path": os.path.join( "quiz_logic","quotes.go"),
            "line": 109,
            "character": 0,
            "text": "func (q *Quoter) GetEditFileQuote() string {\n\treturn \"File has been edited.\"\n}\n"
        },        
        "implementation": {
            "path": os.path.join( "quiz_logic","question.go"),
            "line": 9,
            "character": 7
        }        
    }