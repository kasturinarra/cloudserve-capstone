from dataclasses import dataclass


@dataclass(frozen=True)
class SupportResponse:
    response: str
    source_references: tuple[str, ...]
    machine_generated_disclosure: bool
    grounded: bool
