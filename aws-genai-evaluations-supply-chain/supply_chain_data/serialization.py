"""Pretty-printer and parser for supply chain API payloads."""

from typing import Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def pretty_print(payload: BaseModel) -> str:
    """Serialize a Pydantic payload object to a formatted JSON string.

    Args:
        payload: A Pydantic BaseModel instance to serialize.

    Returns:
        A human-readable, indented JSON string representation of the payload.
    """
    return payload.model_dump_json(indent=2)


def parse_payload(json_str: str, model_class: Type[T]) -> T:
    """Deserialize a JSON string into a typed Pydantic model instance.

    Args:
        json_str: A JSON string to parse.
        model_class: The Pydantic model class to deserialize into.

    Returns:
        An instance of model_class reconstructed from the JSON string.
    """
    return model_class.model_validate_json(json_str)
