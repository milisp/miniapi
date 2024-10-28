def html(content: str) -> str:
    """Helper function to create HTML content with proper doctype"""
    return f"<!DOCTYPE html>\n<html><body>{content}</body></html>"
