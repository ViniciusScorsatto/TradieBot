from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TemplateOption:
    id: str
    name: str
    accent: str
    description: str


TEMPLATES: tuple[TemplateOption, ...] = (
    TemplateOption("classic-blue", "Classic Blue", "#185adb", "Clean corporate layout with a bold blue header."),
    TemplateOption("trade-orange", "Trade Orange", "#e8630a", "High-energy layout for hands-on service businesses."),
    TemplateOption("forest-ledger", "Forest Ledger", "#256d1b", "Calm, trustworthy design with strong totals hierarchy."),
    TemplateOption("graphite-pro", "Graphite Pro", "#2c3639", "Dark neutral look for premium trades and contractors."),
    TemplateOption("sunset-statement", "Sunset Statement", "#c44900", "Warm, modern template with a more creative feel."),
)


def get_template(template_id: str) -> TemplateOption:
    for template in TEMPLATES:
        if template.id == template_id:
            return template
    return TEMPLATES[0]
