#!/usr/bin/env python3
"""Generate dependency-free SVG figures for the GOaudit launch manuscript."""

from __future__ import annotations

import csv
import html
import math
from pathlib import Path
from textwrap import wrap


HERE = Path(__file__).resolve().parent
TABLES = HERE.parent / "tables"

INK = "#17212B"
MUTED = "#52606D"
GRID = "#D9E2EC"
PAPER = "#FFFFFF"
NAVY = "#174A7E"
BLUE = "#2F80B7"
TEAL = "#138A8A"
CORAL = "#E76F51"
GOLD = "#E9A23B"
PALE_BLUE = "#EAF3F8"
PALE_TEAL = "#E7F5F2"
PALE_CORAL = "#FCEDE8"


class SVG:
    def __init__(self, width: int, height: int, title: str):
        self.width = width
        self.height = height
        self.parts = [
            (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
                f'height="{height}" viewBox="0 0 {width} {height}" '
                'role="img" aria-labelledby="title desc">'
            ),
            f"<title id=\"title\">{html.escape(title)}</title>",
            f"<desc id=\"desc\">{html.escape(title)}</desc>",
            f'<rect width="{width}" height="{height}" fill="{PAPER}"/>',
            (
                "<style>"
                "text{font-family:Arial,Helvetica,sans-serif;fill:#17212B}"
                ".title{font-size:31px;font-weight:700}"
                ".panel{font-size:27px;font-weight:700}"
                ".heading{font-size:22px;font-weight:700}"
                ".body{font-size:18px}"
                ".small{font-size:15px;fill:#52606D}"
                ".axis{font-size:16px;fill:#52606D}"
                "</style>"
            ),
        ]

    def rect(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        fill: str,
        stroke: str = "none",
        stroke_width: float = 0,
        rx: float = 0,
    ) -> None:
        self.parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" '
            f'height="{height:.1f}" rx="{rx:.1f}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{stroke_width:.1f}"/>'
        )

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        stroke: str = GRID,
        stroke_width: float = 2,
        dash: str | None = None,
    ) -> None:
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" '
            f'y2="{y2:.1f}" stroke="{stroke}" stroke-width="{stroke_width:.1f}"'
            f"{dash_attr}/>"
        )

    def text(
        self,
        x: float,
        y: float,
        text: str,
        css_class: str = "body",
        anchor: str = "start",
        fill: str | None = None,
        weight: int | None = None,
    ) -> None:
        attrs = [f'class="{css_class}"', f'text-anchor="{anchor}"']
        if fill:
            attrs.append(f'style="fill:{fill}"')
        if weight:
            attrs.append(f'font-weight="{weight}"')
        self.parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" {" ".join(attrs)}>'
            f"{html.escape(str(text))}</text>"
        )

    def multiline(
        self,
        x: float,
        y: float,
        text: str,
        width_chars: int,
        css_class: str = "body",
        line_height: int = 24,
        anchor: str = "start",
    ) -> None:
        lines = wrap(text, width=width_chars, break_long_words=False) or [""]
        self.parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" class="{css_class}" '
            f'text-anchor="{anchor}">'
        )
        for index, line in enumerate(lines):
            dy = 0 if index == 0 else line_height
            self.parts.append(
                f'<tspan x="{x:.1f}" dy="{dy}">{html.escape(line)}</tspan>'
            )
        self.parts.append("</text>")

    def circle(self, cx: float, cy: float, radius: float, fill: str, stroke: str = "none") -> None:
        self.parts.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" '
            f'fill="{fill}" stroke="{stroke}"/>'
        )

    def polyline(
        self,
        points: list[tuple[float, float]],
        stroke: str,
        stroke_width: float = 4,
        fill: str = "none",
    ) -> None:
        value = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        self.parts.append(
            f'<polyline points="{value}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{stroke_width:.1f}" stroke-linejoin="round" '
            'stroke-linecap="round"/>'
        )

    def arrow(self, x1: float, y1: float, x2: float, y2: float, color: str = NAVY) -> None:
        self.line(x1, y1, x2, y2, color, 5)
        angle = math.atan2(y2 - y1, x2 - x1)
        length = 18
        spread = 0.55
        points = [(x2, y2)]
        for offset in (math.pi - spread, math.pi + spread):
            points.append(
                (
                    x2 + length * math.cos(angle + offset),
                    y2 + length * math.sin(angle + offset),
                )
            )
        value = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        self.parts.append(f'<polygon points="{value}" fill="{color}"/>')

    def save(self, path: Path) -> None:
        path.write_text("\n".join([*self.parts, "</svg>\n"]), encoding="utf-8")


def read_tsv(name: str) -> list[dict[str, str]]:
    with (TABLES / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def figure1() -> None:
    svg = SVG(1800, 950, "GOaudit workflow")
    svg.text(70, 70, "GOaudit adds a taxonomic checkpoint before interpretation", "title")

    card_y, card_h = 190, 400
    cards = [
        (70, 330, PALE_BLUE, "1", "Generate GO terms", [
            "Orthology transfer",
            "Protein signatures",
            "Machine-learning prediction",
        ]),
        (480, 280, "#F5F7FA", "2", "Standardize", [
            "protein_id    go_id",
            "One association per row",
            "Any annotation source",
        ]),
        (840, 370, PALE_TEAL, "3", "Audit with GOaudit", [
            "Target NCBI taxid",
            "Complete taxonomic lineage",
            "Dated GO constraints",
            "Alternative / obsolete IDs",
        ]),
        (1290, 430, PALE_CORAL, "4", "Review and use", [
            "Association-level decisions",
            "Summary statistics + plots",
            "Optional filtered table",
            "Enrichment / OrgDb",
        ]),
    ]
    for x, width, fill, number, heading, bullets in cards:
        svg.rect(x, card_y, width, card_h, fill, GRID, 2, 18)
        svg.circle(x + 42, card_y + 45, 24, NAVY)
        svg.text(x + 42, card_y + 52, number, "body", "middle", PAPER, 700)
        svg.text(x + 78, card_y + 53, heading, "heading")
        for index, bullet in enumerate(bullets):
            yy = card_y + 125 + index * 61
            svg.circle(x + 42, yy - 6, 5, TEAL if number == "3" else BLUE)
            svg.multiline(x + 60, yy, bullet, max(20, int(width / 12)), "body", 23)

    svg.arrow(410, 390, 463, 390)
    svg.arrow(760, 390, 823, 390)
    svg.arrow(1210, 390, 1273, 390)

    svg.rect(580, 690, 640, 130, "#F8FAFC", GRID, 2, 14)
    svg.text(610, 730, "Reference provenance retained with every run", "heading")
    svg.multiline(
        610,
        770,
        "Source URLs • retrieval time • release identifiers • SHA-256 checksums",
        65,
        "body",
    )
    svg.arrow(1025, 675, 1025, 610, MUTED)
    svg.text(
        900,
        890,
        "Protein evidence is preserved; only incompatible protein–GO associations are flagged.",
        "small",
        "middle",
    )
    svg.save(HERE / "figure1_workflow.svg")


def horizontal_bars(
    svg: SVG,
    rows: list[tuple[str, int]],
    x: float,
    y: float,
    width: float,
    bar_height: float,
    gap: float,
    color: str,
    label_width: int,
    max_value: int | None = None,
) -> None:
    maximum = max_value or max(value for _, value in rows)
    label_x = x
    bar_x = x + label_width
    bar_width = width - label_width - 70
    for index, (label, value) in enumerate(rows):
        yy = y + index * (bar_height + gap)
        svg.text(label_x, yy + bar_height * 0.72, label, "axis")
        svg.rect(bar_x, yy, bar_width, bar_height, "#EDF2F7", rx=4)
        svg.rect(bar_x, yy, bar_width * value / maximum, bar_height, color, rx=4)
        svg.text(bar_x + bar_width + 12, yy + bar_height * 0.72, f"{value:,}", "axis")


def figure2() -> None:
    terms_raw = read_tsv("table_3_top_violations.tsv")
    terms = [(row["description"], int(row["associations"])) for row in terms_raw]
    taxa_raw = read_tsv("table_s3_constraint_taxa.tsv")[:8]
    taxa = [(row["constraint_taxon"], int(row["associations"])) for row in taxa_raw]

    svg = SVG(2200, 1450, "Frequent taxon-incompatible DeepGOPlus predictions")
    svg.text(
        70,
        70,
        "Frequent taxon-incompatible DeepGOPlus predictions in Stylophora pistillata",
        "title",
    )
    svg.text(70, 130, "A", "panel")
    svg.text(115, 130, "Most frequent incompatible GO terms", "heading")
    horizontal_bars(svg, terms, 85, 180, 1240, 40, 23, CORAL, 430)

    svg.line(1390, 130, 1390, 1270, GRID, 3)
    svg.text(1450, 130, "B", "panel")
    svg.text(1495, 130, "Most frequent constraint taxa", "heading")
    horizontal_bars(svg, taxa, 1460, 210, 650, 48, 42, TEAL, 185)

    svg.rect(1450, 990, 650, 200, "#F8FAFC", GRID, 2, 12)
    svg.text(1480, 1032, "Interpretation", "heading")
    svg.multiline(
        1480,
        1072,
        "Counts are protein–GO associations after DeepGOPlus propagation to GO ancestors. They are not independent experimental function calls.",
        57,
        "body",
        28,
    )
    svg.text(
        70,
        1375,
        "Predictions retained at combined DeepGOPlus score ≥0.30; GOaudit GO release 15 June 2026.",
        "small",
    )
    svg.save(HERE / "figure2_deepgoplus_violations.svg")


def figure3() -> None:
    rows = read_tsv("table_s1_score_thresholds.tsv")[:6]
    thresholds = [float(row["minimum_score"]) for row in rows]
    violations = [int(row["taxon_violations"]) for row in rows]
    rates = [float(row["violation_rate_percent"]) for row in rows]

    svg = SVG(1800, 1100, "DeepGOPlus score threshold sensitivity")
    svg.text(70, 70, "Score thresholding does not substitute for a taxon audit", "title")
    svg.text(80, 130, "Taxon-incompatible associations", "heading")
    svg.text(1710, 130, "Violation rate (%)", "heading", "end")

    plot_x, plot_y, plot_w, plot_h = 180, 190, 1420, 650
    max_count, max_rate = 9000, 0.9
    for tick in range(0, 9001, 1500):
        yy = plot_y + plot_h - plot_h * tick / max_count
        svg.line(plot_x, yy, plot_x + plot_w, yy, GRID, 2)
        svg.text(plot_x - 20, yy + 6, f"{tick:,}", "axis", "end")
    for tick in (0, 0.15, 0.30, 0.45, 0.60, 0.75, 0.90):
        yy = plot_y + plot_h - plot_h * tick / max_rate
        svg.text(plot_x + plot_w + 20, yy + 6, f"{tick:.2f}", "axis")

    step = plot_w / len(rows)
    bar_width = step * 0.48
    line_points: list[tuple[float, float]] = []
    for index, (threshold, count, rate) in enumerate(zip(thresholds, violations, rates)):
        cx = plot_x + step * (index + 0.5)
        bar_h = plot_h * count / max_count
        svg.rect(cx - bar_width / 2, plot_y + plot_h - bar_h, bar_width, bar_h, BLUE, rx=5)
        svg.text(cx, plot_y + plot_h + 46, f"≥{threshold:.2f}", "axis", "middle")
        svg.text(
            cx,
            plot_y + plot_h - bar_h - 14,
            f"{count:,}",
            "axis",
            "middle",
        )
        line_y = plot_y + plot_h - plot_h * rate / max_rate
        line_points.append((cx, line_y))
    svg.polyline(line_points, CORAL, 5)
    for (cx, cy), rate in zip(line_points, rates):
        svg.circle(cx, cy, 9, CORAL, PAPER)
        svg.text(cx, cy - 18, f"{rate:.3f}%", "axis", "middle")

    svg.text(plot_x + plot_w / 2, 930, "Minimum DeepGOPlus combined score", "heading", "middle")

    svg.rect(970, 235, 555, 105, PALE_CORAL, CORAL, 2, 12)
    svg.text(995, 275, "2,306 incompatible associations", "heading")
    svg.text(995, 310, "remain at score ≥0.65", "body")
    svg.arrow(1240, 355, line_points[4][0], plot_y + plot_h - 20, CORAL)

    svg.rect(80, 980, 1640, 70, "#F8FAFC", GRID, 2, 10)
    svg.text(
        900,
        1023,
        "Bars: incompatible association count    •    Line: incompatible percentage among all associations retained",
        "small",
        "middle",
    )
    svg.save(HERE / "figure3_score_thresholds.svg")


def main() -> None:
    figure1()
    figure2()
    figure3()
    print("Wrote figure1_workflow.svg")
    print("Wrote figure2_deepgoplus_violations.svg")
    print("Wrote figure3_score_thresholds.svg")


if __name__ == "__main__":
    main()
