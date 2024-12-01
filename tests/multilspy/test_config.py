"""
Configuration values for language server tests
"""
from multilspy.multilspy_config import Language

TEST_REPO = {
    "url": "https://github.com/CJFEdu/lsp_test_project/",
    "commit": "5bae14332e090636f87a2ddf404e55c31e66bb94"
}

def setup_test_params(code_language: Language) -> dict:
    """
    Setup test parameters for language server tests
    
    Args:
        code_language: The language to setup parameters for
        
    Returns:
        Dictionary containing test parameters
    """
    return {
        "code_language": code_language,
        "repo_url": TEST_REPO["url"],
        "repo_commit": TEST_REPO["commit"]
    }

