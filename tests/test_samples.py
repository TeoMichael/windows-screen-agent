from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_sample_form_is_available():
    sample = ROOT / "samples" / "sample_form.html"

    assert sample.exists()
    assert "Windows Screen Agent Sample Form" in sample.read_text(encoding="utf-8")


def test_samples_readme_mentions_demo_and_pytest():
    readme = (ROOT / "samples" / "README.md").read_text(encoding="utf-8")

    assert "windows-screen-agent demo" in readme
    assert "python -m pytest -q" in readme
