"""Common reusable mixins for Pydantic schemas."""

from datetime import datetime, date, time
from typing import Optional, Any, List, Dict, get_origin, get_args

from pydantic import BaseModel, ConfigDict, Field


class FromOrmAttributesConfig(BaseModel):
    """
    Base schema with ORM support via `from_attributes`.

    Adds reading the instance attributes corresponding to the model field names.
    Provides integration with object-relational mappings (ORMs).
    """

    model_config = ConfigDict(from_attributes=True)


class IdMixin(BaseModel):
    """Mixin adding an integer `id` field."""

    id: int = Field(json_schema_extra={"example": 1})


class TimestampsMixin(BaseModel):
    """Mixin adding optional `created_at` and `updated_at` timestamps."""

    created_at: Optional[datetime] = Field(
        None,
        description="Record creation timestamp",
        json_schema_extra={"example": "2025-01-01T12:00:00.392Z"},
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="Record last update timestamp",
        json_schema_extra={"example": "2025-01-01T13:00:00.392Z"},
    )


class InfoMixin(BaseModel):
    """Mixin adding an optional `info` field for free-form notes."""

    info: Optional[str] = Field(
        None,
        description="Additional descriptive notes",
        json_schema_extra={
            "example": (
                "Works in automotive. Met at conference in Prague 13.08.2025.\n"
                "Loves cats, allergic to nuts and cocoa."
            )
        },
    )


class UserRoleMixin(BaseModel):
    """Mixin adding an optional `role` field for user roles."""

    role: Optional[str] = Field(
        None,
        description="User role (e.g., admin, user)",
        json_schema_extra={"example": "admin"},
    )


class ContactsCountMixin(BaseModel):
    """Mixin adding a `contacts_count` integer field."""

    contacts_count: int = Field(
        0,
        description="Number of associated contacts",
        json_schema_extra={"example": 42},
    )


class ExampleMixin(BaseModel):
    """Mixin providing methods to generate example payloads from schema fields."""

    @classmethod
    def generate_example(cls) -> Dict:
        """Generate a flat example dictionary from field `json_schema_extra` examples."""
        example = {}
        for name, field in cls.model_fields.items():
            extra = getattr(field, "json_schema_extra", None)
            if isinstance(extra, Dict) and "example" in extra:
                example[name] = extra["example"]
            elif hasattr(field, "default") and field.default is not None:
                example[name] = field.default
        return example

    @classmethod
    def generate_example_recursive(cls) -> Dict[str, Any]:
        """Generate example recursively, handling nested models, lists, dicts, and date/time fields."""
        example = {}
        for name, field in cls.model_fields.items():
            value: Any = None

            # 1. Values from json_schema_extra
            extra = getattr(field, "json_schema_extra", None)
            if isinstance(extra, Dict) and "example" in extra:
                value = extra["example"]
            elif getattr(field, "default", None) is not None:
                value = field.default

            # 2. For submodules, recursively
            field_type = getattr(field, "annotation", None)
            origin = get_origin(field_type)
            args = get_args(field_type)

            if hasattr(field_type, "model_fields"):
                value = field_type.generate_example_recursive()  # type: ignore
            elif origin in (list, List) and args:
                sub_type = args[0]
                if hasattr(sub_type, "generate_example_recursive"):
                    value = [sub_type.generate_example_recursive()]
                elif sub_type:
                    value = [None]
            elif origin in (dict, Dict) and len(args) == 2:
                val_type = args[1]
                if hasattr(val_type, "generate_example_recursive"):
                    value = {"key": val_type.generate_example_recursive()}
                else:
                    value = {"key": None}

            # 3. datetime/date/time → ISO-string
            if isinstance(value, (datetime, date, time)):
                value = value.isoformat()

            example[name] = value

        return example
