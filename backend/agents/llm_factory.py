"""LLM factory for creating chat models from any supported provider.

Pass a model name string (e.g. "claude-sonnet-4-5-20250929", "gpt-5.2",
"gemini-2.5-flash") and the factory resolves it to the correct LangChain
chat model class based on the name prefix.
"""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI


MODEL_PREFIXES: list[tuple[tuple[str, ...], type[BaseChatModel]]] = [
    (("gpt-",),    ChatOpenAI),
    (("claude-",), ChatAnthropic),
    (("gemini-",), ChatGoogleGenerativeAI),
]

SUPPORTED_MODELS: dict[str, list[str]] = {
    "openai": [
        "gpt-5.3-codex",
        "gpt-5.2",
        "gpt-5.1",
        "gpt-4.1",
        "gpt-4o",
    ],
    "anthropic": [
        "claude-opus-4-6",
        "claude-sonnet-4-6",
        "claude-sonnet-4-5-20250929",
        "claude-opus-4-5-20251101",
        "claude-haiku-4-5-20251001",
    ],
    "google": [
        "gemini-3.1-pro-preview",
        "gemini-3-flash-preview",
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
    ],
}


def create_llm(model: str, **kwargs) -> BaseChatModel:
    """Create a chat model instance from a model name string.

    The provider is determined by the model name prefix:
      - gpt-*    -> ChatOpenAI   (needs OPENAI_API_KEY)
      - claude-* -> ChatAnthropic (needs ANTHROPIC_API_KEY)
      - gemini-* -> ChatGoogleGenerativeAI (needs GOOGLE_API_KEY)

    Args:
        model: The model name (e.g. "claude-sonnet-4-5-20250929").
        **kwargs: Extra arguments forwarded to the model constructor
                  (e.g. temperature=0).

    Returns:
        A configured BaseChatModel instance.

    Raises:
        ValueError: If the model name doesn't match any known provider prefix.
    """
    for prefixes, cls in MODEL_PREFIXES:
        if any(model.startswith(p) for p in prefixes):
            return cls(model=model, **kwargs)

    all_prefixes = ", ".join(p for prefixes, _ in MODEL_PREFIXES for p in prefixes)
    raise ValueError(
        f"Unknown model '{model}'. Expected a name starting with one of: {all_prefixes}"
    )
