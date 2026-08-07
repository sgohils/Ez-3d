from __future__ import annotations

import json
import os
import sys
from typing import Any, Sequence

from backend.dataset.prompt_templates import (
    DifficultyLevel,
    PromptTemplate,
    get_templates,
    sample_template,
)
from backend.dataset.validate_scripts import ScriptValidationError, validate_script


def generate_dataset(
    count: int = 120,
    difficulty: DifficultyLevel | None = None,
    templates: Sequence[PromptTemplate] | None = None,
    output_path: str = "dataset.jsonl",
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    seen_signatures: set[str] = set()
    validation_errors: list[dict[str, Any]] = []

    pool = list(templates) if templates else list(get_templates(difficulty))
    if not pool:
        pool = list(get_templates(None))

    generated = 0
    attempts = 0
    max_attempts = count * 10

    while generated < count and attempts < max_attempts:
        attempts += 1
        tmpl = pool[attempts % len(pool)]
        from backend.dataset.prompt_templates import generate_entry
        entry = generate_entry(template=tmpl)

        signature = json.dumps(entry["metadata"]["params"], sort_keys=True)
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)

        try:
            validate_script(entry["code"])
            entries.append(entry)
            generated += 1
        except ScriptValidationError as exc:
            validation_errors.append({
                "template_id": entry["metadata"]["template_id"],
                "error": str(exc),
                "logs": exc.logs,
                "code": entry["code"],
            })

    dataset = {
        "entries": entries,
        "stats": {
            "requested": count,
            "generated": len(entries),
            "validation_failures": len(validation_errors),
            "total_attempts": attempts,
        },
        "validation_errors": validation_errors,
    }

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return dataset


def main(argv: Sequence[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    count = 120
    output_path = "dataset.jsonl"
    difficulty = None

    args = list(argv)
    i = 0
    while i < len(args):
        if args[i] == "--count" and i + 1 < len(args):
            count = int(args[i + 1])
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            output_path = args[i + 1]
            i += 2
        elif args[i] == "--difficulty" and i + 1 < len(args):
            difficulty = DifficultyLevel(args[i + 1])
            i += 2
        else:
            i += 1

    print(f"Generating {count} entries -> {output_path}")
    dataset = generate_dataset(count=count, difficulty=difficulty, output_path=output_path)
    stats = dataset["stats"]
    print(f"Generated {stats['generated']}/{stats['requested']} validated entries")
    print(f"Validation failures: {stats['validation_failures']}")
    print(f"Total attempts: {stats['total_attempts']}")
    if dataset["validation_errors"]:
        print("Sample validation errors:")
        for err in dataset["validation_errors"][:5]:
            print(f"  - {err['template_id']}: {err['error']}")
    if stats["generated"] < count:
        print("WARNING: fewer entries generated than requested")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
