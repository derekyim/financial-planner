"""LangChain tools for building Google Slides presentations.

These tools let the presentation agent create new presentations and add
slides based on insights from the financial analysis conversation.
"""

import os
from typing import Optional
from langchain_core.tools import tool

from shared.slides_utilities import SlidesUtilities

_slides_client: Optional[SlidesUtilities] = None
_active_presentation_id: Optional[str] = None
_active_presentation_url: Optional[str] = None


def initialize_presentation_tools(credentials_path: str) -> None:
    """Initialize the slides client."""
    global _slides_client
    _slides_client = SlidesUtilities(credentials_path)


def _get_client() -> SlidesUtilities:
    if _slides_client is None:
        raise RuntimeError(
            "Presentation tools not initialized. "
            "Call initialize_presentation_tools() first."
        )
    return _slides_client


def _get_presentation_id() -> str:
    if not _active_presentation_id:
        raise RuntimeError(
            "No active presentation. Call create_presentation first."
        )
    return _active_presentation_id


def get_active_presentation_url() -> Optional[str]:
    """Return the URL of the most recently created presentation, if any."""
    return _active_presentation_url


@tool
def create_presentation(title: str) -> str:
    """Create a new Google Slides presentation.

    ALWAYS call this first before adding any slides. It creates a fresh
    presentation and returns the shareable URL.

    Args:
        title: The presentation title (shown in Google Drive and the title bar).

    Returns:
        The URL of the new presentation.
    """
    global _active_presentation_id, _active_presentation_url
    try:
        client = _get_client()
        pres_id, url = client.create_presentation(title)
        _active_presentation_id = pres_id
        _active_presentation_url = url
        return f"Presentation created: {url}"
    except Exception as e:
        return f"Error creating presentation: {e}"


@tool
def add_title_slide(title: str, subtitle: str = "") -> str:
    """Add a title slide to the active presentation.

    Use this for the opening slide or section dividers.

    Args:
        title: The main title text.
        subtitle: Optional subtitle text.

    Returns:
        Confirmation message.
    """
    try:
        client = _get_client()
        pres_id = _get_presentation_id()
        client.add_title_slide(pres_id, title, subtitle)
        return f"Title slide added: \"{title}\""
    except Exception as e:
        return f"Error adding title slide: {e}"


@tool
def add_content_slide(title: str, body: str) -> str:
    """Add a slide with a title and paragraph body text.

    Use this for slides that present analysis, insights, or explanations
    in paragraph form.

    Args:
        title: The slide title.
        body: The body text content (can include line breaks).

    Returns:
        Confirmation message.
    """
    try:
        client = _get_client()
        pres_id = _get_presentation_id()
        client.add_content_slide(pres_id, title, body)
        return f"Content slide added: \"{title}\""
    except Exception as e:
        return f"Error adding content slide: {e}"


@tool
def add_bullet_slide(title: str, bullets: list[str]) -> str:
    """Add a slide with a title and bullet points.

    Use this for slides that list key points, recommendations, or metrics.

    Args:
        title: The slide title.
        bullets: List of bullet point strings.

    Returns:
        Confirmation message.
    """
    try:
        client = _get_client()
        pres_id = _get_presentation_id()
        client.add_bullet_slide(pres_id, title, bullets)
        return f"Bullet slide added: \"{title}\" with {len(bullets)} points"
    except Exception as e:
        return f"Error adding bullet slide: {e}"


@tool
def get_presentation_info() -> str:
    """Get the current slide count and URL of the active presentation.

    Returns:
        Slide count and URL.
    """
    try:
        client = _get_client()
        pres_id = _get_presentation_id()
        count = client.get_slide_count(pres_id)
        url = _active_presentation_url or "unknown"
        return f"{count} slides — {url}"
    except Exception as e:
        return f"Error reading presentation: {e}"


PRESENTATION_TOOLS = [
    create_presentation,
    add_title_slide,
    add_content_slide,
    add_bullet_slide,
    get_presentation_info,
]
