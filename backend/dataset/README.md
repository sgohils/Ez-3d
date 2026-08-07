# Synthetic Dataset Generation Pipeline

Generates a JSONL dataset of validated CadQuery scripts with multi-level prompts for fine-tuning.

## Files

- `prompt_templates.py` — parametric prompt/script templates for 12 CAD primitives
- `validate_scripts.py` — headless execution validator (subprocess-based)
- `generate_dataset.py` — orchestrator: sample → validate → filter → JSONL

## Usage

```bash
cd backend
python -m dataset.generate_dataset --count 120 --output dataset/dataset.jsonl
```

## Output

Each line is a JSON object:

```json
{
  "instruction": "Create a rectangular box with length 80, width 60, and height 10.",
  "code": "import cadquery as cq\n\nlength: float = 80\n...",
  "metadata": {
    "template_id": "box",
    "difficulty": "beginner",
    "params": {"length": 80, "width": 60, "height": 10},
    "param_specs": [...]
  }
}
```

## Requirements

- Python 3.9+
- cadquery>=2.4.0
- Dependencies listed in `backend/requirements.txt`

## Scaling

Increase `--count` to scale toward 10k+ entries. Templates are sampled with replacement avoidance to maximize diversity.
