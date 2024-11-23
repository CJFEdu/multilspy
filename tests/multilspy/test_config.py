"""
Configuration values for language server tests
"""
from multilspy.multilspy_config import Language

TEST_REPO = {
    "url": "https://github.com/CJFEdu/lsp_test_project/",
    "commit": "1745076eb7aac032a47e01822e0e395e64e9d7ff"
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
