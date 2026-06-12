"""letz CLI — Command-line interface for Luxembourgish language tools."""

from __future__ import annotations

import sys

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from letz.spellchecker import Spellchecker
from letz.normalizer import Normalizer
from letz.lod import LODClient
from letz.llm_context import generate_llm_context, generate_spellcheck_prompt, generate_normalization_prompt

console = Console()


def _display_check_result(result):
    """Display spellcheck results in a Rich table."""
    if not result.errors and not result.warnings:
        console.print("[green]✓ No spelling errors found.[/green]")
        return

    if result.errors:
        console.print(f"[red]Found {result.error_count} error(s):[/red]")
        for error in result.errors:
            console.print(f"  [red]✗[/red] [bold]{error.word}[/bold]")
            if error.suggestions:
                console.print(f"    → [green]{', '.join(error.suggestions)}[/green]")
            if error.rule_violations:
                console.print(f"    [dim]{'; '.join(error.rule_violations)}[/dim]")

    if result.warnings:
        console.print(f"[yellow]Found {result.warning_count} warning(s):[/yellow]")
        for warning in result.warnings:
            console.print(f"  [yellow]⚠[/yellow] [bold]{warning.word}[/bold]")
            if warning.rule_violations:
                console.print(f"    [dim]{'; '.join(warning.rule_violations)}[/dim]")
            if warning.notes:
                console.print(f"    [dim]{'; '.join(warning.notes)}[/dim]")


@click.group()
@click.version_option(version="0.1.0", prog_name="letz")
def main():
    """🇱🇺 letz — Luxembourgish language tools.

    Spellchecker, normalizer, and LLM context generator for Lëtzebuergesch.
    """
    pass


@main.command()
@click.argument("text", nargs=-1, required=True)
@click.option("--offline", is_flag=True, help="Skip LOD dictionary lookup (offline mode)")
@click.option("--strict", is_flag=True, help="Flag unknown words as errors (default: warnings)")
@click.option("--json-output", "json_out", is_flag=True, help="Output as JSON")
def check(text, offline, strict, json_out):
    """Check Luxembourgish text for spelling errors.

    \b
    Examples:
        letz check "D'Lëtzebuerger Sprooch ass schéin"
        letz check --offline "Ech sinn Lëtzebuerger"
        letz check --strict "D'Letzebuerg Sprooch"
    """
    input_text = " ".join(text)
    checker = Spellchecker(use_lod=not offline, strict=strict)

    try:
        result = checker.check_text(input_text)

        if json_out:
            import json
            output = {
                "text": result.original,
                "error_count": result.error_count,
                "warning_count": result.warning_count,
                "errors": [
                    {
                        "word": r.word,
                        "is_valid": r.is_valid,
                        "suggestions": r.suggestions,
                        "rule_violations": r.rule_violations,
                        "notes": r.notes,
                    }
                    for r in result.words
                    if not r.is_valid or r.rule_violations
                ],
            }
            click.echo(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            _display_check_result(result)
    finally:
        checker.close()


@main.command()
@click.argument("text", nargs=-1, required=True)
@click.option("--json-output", "json_out", is_flag=True, help="Output as JSON")
def normalize(text, json_out):
    """Normalize Luxembourgish text to standard spelling.

    Converts variant spellings, German-influenced forms, and ß to
    standard Luxembourgish orthography.

    \b
    Examples:
        letz normalize "Feebruar"
        letz normalize "Straße"
    """
    input_text = " ".join(text)
    norm = Normalizer()
    result = norm.normalize(input_text)

    if json_out:
        import json
        click.echo(json.dumps({"input": input_text, "normalized": result}, ensure_ascii=False, indent=2))
    else:
        if input_text == result:
            console.print(f"[green]✓[/green] Already standard: {result}")
        else:
            console.print(f"[yellow]Input:[/yellow]    {input_text}")
            console.print(f"[green]Normalized:[/green] {result}")


@main.command()
@click.argument("word")
@click.option("--json-output", "json_out", is_flag=True, help="Output as JSON")
def lookup(word, json_out):
    """Look up a word in the LOD (Lëtzebuerger Online Dictionnaire).

    \b
    Examples:
       letz lookup "Haus"
        letz lookup "Sprooch"
    """
    lod = LODClient()
    try:
        result = lod.check_spelling(word)

        if json_out:
            import json
            click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if result["found"]:
                console.print(f"[green]✓[/green] '{word}' found in LOD dictionary")
                if result.get("entry"):
                    console.print(Panel(str(result["entry"]), title=f"Entry: {word}"))
            else:
                console.print(f"[red]✗[/red] '{word}' not found in LOD dictionary")
                if result.get("suggestions"):
                    console.print(f"[yellow]Suggestions:[/yellow] {', '.join(result['suggestions'])}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    finally:
        lod.close()


@main.command()
@click.argument("text", nargs=-1, required=True)
@click.option("--focus", multiple=True, help="Focus areas: vowels, consonants, n-rule, diphthongs, foreign-words, capitalization")
@click.option("--mode", type=click.Choice(["spellcheck", "normalize"]), default="spellcheck", help="Prompt mode")
@click.option("--detailed/--compact", default=True, help="Include full rule explanations")
@click.option("--copy", is_flag=True, help="Copy prompt to clipboard")
def prompt(text, focus, mode, detailed, copy):
    """Generate an LLM prompt with Luxembourgish orthography context.

    This is the key feature: inject orthography rules into an LLM prompt
    so the model can spellcheck Luxembourgish even without training data.

    \b
    Examples:
        letz prompt "Ech hunn d'Bouf gesinn"
        letz prompt --focus n-rule --focus vowels "E schéint Meedchen"
        letz prompt --mode normalize "Feebruar"
    """
    input_text = " ".join(text)
    focus_areas = list(focus) if focus else None

    if mode == "spellcheck":
        result = generate_spellcheck_prompt(input_text, focus_areas=focus_areas, detailed=detailed)
    else:
        result = generate_normalization_prompt(input_text)

    if copy:
        try:
            import subprocess
            subprocess.run(["xclip", "-selection", "clipboard"], input=result.encode(), check=True)
            console.print("[green]✓[/green] Prompt copied to clipboard")
        except (ImportError, subprocess.CalledProcessError):
            try:
                import subprocess
                subprocess.run(["pbcopy"], input=result.encode(), check=True)
                console.print("[green]✓[/green] Prompt copied to clipboard")
            except (ImportError, subprocess.CalledProcessError):
                console.print("[yellow]Could not copy to clipboard. Displaying prompt:[/yellow]")
                console.print(result)
    else:
        console.print(result)


@main.command()
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="Output format")
def rules(format):
    """Display the Luxembourgish orthography rules.

    Shows the structured rules from the official 2024 CPLL/ZLS specification.
    """
    from letz.rules import load_orthography_rules
    ortho = load_orthography_rules()

    if format == "json":
        import json
        click.echo(json.dumps(ortho, ensure_ascii=False, indent=2, default=str))
    else:
        console.print(Panel(
            f"[bold]{ortho['title']}[/bold]\n"
            f"{ortho['edition']}\n"
            f"Published by: {ortho['publisher']}",
            title="🇱🇺 Luxembourgish Orthography Rules",
        ))

        for ch_num, ch_data in ortho["chapters"].items():
            console.print(f"\n[bold cyan]Chapter {ch_num}: {ch_data['title_lb']}[/bold cyan]")
            console.print(f"[dim]{ch_data['title_en']}[/dim]")

            rules_data = ch_data.get("rules", {})
            if isinstance(rules_data, dict):
                for key, value in rules_data.items():
                    if isinstance(value, str):
                        console.print(f"  • [bold]{key}[/bold]: {value}")
                    elif isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if isinstance(sub_value, str):
                                console.print(f"  • [bold]{sub_key}[/bold]: {sub_value}")


@main.command()
def variants():
    """List accepted spelling variants for Luxembourgish words.

    Shows words that have multiple accepted spellings and their
    standard (recommended) form.
    """
    from letz.rules import load_spelling_variants
    sv = load_spelling_variants()

    table = Table(title="🇱🇺 Luxembourgish Spelling Variants")
    table.add_column("Standard Form", style="green bold")
    table.add_column("Accepted Variants", style="yellow")

    for standard, variant_list in sv.items():
        variants_str = ", ".join(variant_list)
        table.add_row(standard, variants_str)

    console.print(table)


if __name__ == "__main__":
    main()