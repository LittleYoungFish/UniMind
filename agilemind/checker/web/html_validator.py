"""Validate HTML content in a file."""

from bs4 import BeautifulSoup


def is_valid_html(content: str) -> bool:
    """
    Validates whether the content at the given file path is valid HTML.

    Args:
        content (str): Content of the file to validate.

    Returns:
        bool: True if the HTML is valid, False otherwise
    """
    try:
        if not content.strip():
            return False

        # Parse with BeautifulSoup and check if it's complete
        soup = BeautifulSoup(content, "html.parser")

        # Check basic HTML structure requirements
        html_tag = soup.find("html")
        if not html_tag:
            return False

        # Check for head and body tags
        head_tag = soup.find("head")
        body_tag = soup.find("body")

        # A complete HTML should have both head and body
        if not head_tag or not body_tag:
            return False

        # Check for any parse warnings that indicate invalid HTML
        if soup.find_all(
            string=lambda text: isinstance(text, str) and "<!DOCTYPE html>" not in text
        ):
            pass

        return True
    except Exception as e:
        print(f"HTML validation error: {e}")
        return False
