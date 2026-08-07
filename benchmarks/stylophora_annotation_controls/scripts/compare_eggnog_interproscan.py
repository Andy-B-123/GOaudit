#!/usr/bin/env python3
"""How much information does a taxon-controlled eggNOG-mapper run add to InterProScan?

eggNOG-mapper propagates GO ancestors while InterProScan reports signature-level
mappings, so exact protein-GO pair matching understates agreement between the
two. This script therefore reports both exact overlap and overlap under
ancestor closure, and summarises the eggNOG-mapper-only remainder by ontology
depth so that generic terms are not counted as substantive contributions.

Usage:
    python compare_eggnog_interproscan.py EGGNOG_DIR INTERPRO_DIR [--out PREFIX]

Each directory must contain a GOaudit `audit.tsv` (in a `goaudit/`
subdirectory or directly). Only usable rows are compared, so obsolete terms
and taxon violations do not inflate either side. Usable means status `valid`
or `alternate_id`: the latter is a current, taxonomically compatible
annotation that merely arrived under a resolved alternate GO identifier, and
GOaudit's own `valid_rows` summary statistic counts it as such.
"""

from __future__ import annotations

import argparse
from collections import defaultdict, deque
from pathlib import Path

DEFAULT_OBO = Path("/scratch3/bac050/2026_bioinfo_tool/goaudit_cache/go.obo")
ROOTS = ("GO:0008150", "GO:0003674", "GO:0005575")
SPECIFIC_DEPTH = 5


def load_obo(path: Path):
    """Return (parents, names) using is_a and part_of edges."""
    parents: dict[str, set[str]] = defaultdict(set)
    names: dict[str, str] = {}
    current = None
    in_term = False
    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            line = raw.rstrip("\n")
            if line.startswith("["):
                in_term = line == "[Term]"
                current = None
                continue
            if not in_term or ": " not in line:
                continue
            key, value = line.split(": ", 1)
            if key == "id":
                current = value if value.startswith("GO:") else None
            elif current is None:
                continue
            elif key == "name":
                names[current] = value
            elif key == "is_a":
                parents[current].add(value.split()[0])
            elif key == "relationship":
                bits = value.split()
                if len(bits) >= 2 and bits[0] == "part_of":
                    parents[current].add(bits[1])
    return parents, names


def depth_map(parents: dict[str, set[str]]) -> dict[str, int]:
    """Shortest is_a/part_of distance from a namespace root."""
    children: dict[str, set[str]] = defaultdict(set)
    for child, pars in parents.items():
        for parent in pars:
            children[parent].add(child)
    depth: dict[str, int] = {}
    queue = deque((root, 0) for root in ROOTS)
    while queue:
        node, dist = queue.popleft()
        if node in depth and depth[node] <= dist:
            continue
        depth[node] = dist
        for child in children.get(node, ()):
            queue.append((child, dist + 1))
    return depth


def ancestors(term: str, parents, cache: dict[str, set[str]]) -> set[str]:
    """Reflexive ancestor closure."""
    hit = cache.get(term)
    if hit is not None:
        return hit
    seen = {term}
    stack = [term]
    while stack:
        node = stack.pop()
        for parent in parents.get(node, ()):
            if parent not in seen:
                seen.add(parent)
                stack.append(parent)
    cache[term] = seen
    return seen


def find_audit(directory: Path) -> Path:
    for candidate in (directory / "goaudit" / "audit.tsv", directory / "audit.tsv"):
        if candidate.exists():
            return candidate
    raise SystemExit(f"no audit.tsv under {directory}")


USABLE = {"valid", "alternate_id"}


def read_valid_pairs(path: Path) -> set[tuple[str, str]]:
    """Usable protein-GO pairs, keyed on GOaudit's resolved GO identifier."""
    pairs = set()
    with path.open(encoding="utf-8") as handle:
        header = handle.readline().rstrip("\n").split("\t")
        index = {name: i for i, name in enumerate(header)}
        p_col, g_col, s_col = index["protein_id"], index["go_id"], index["status"]
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            if len(fields) > s_col and fields[s_col] in USABLE:
                pairs.add((fields[p_col], fields[g_col]))
    return pairs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("eggnog_dir", type=Path)
    ap.add_argument("interpro_dir", type=Path)
    ap.add_argument("--obo", type=Path, default=DEFAULT_OBO)
    ap.add_argument("--out", type=Path, default=None,
                    help="write TSV summary and eggNOG-only term list to this prefix")
    args = ap.parse_args()

    parents, names = load_obo(args.obo)
    depth = depth_map(parents)

    egg = read_valid_pairs(find_audit(args.eggnog_dir))
    ipr = read_valid_pairs(find_audit(args.interpro_dir))

    ipr_by_protein: dict[str, set[str]] = defaultdict(set)
    for protein, term in ipr:
        ipr_by_protein[protein].add(term)

    cache: dict[str, set[str]] = {}
    closure = {
        protein: set().union(*(ancestors(t, parents, cache) for t in terms))
        for protein, terms in ipr_by_protein.items()
    }

    exact = egg & ipr
    novel: list[tuple[str, str]] = []
    for protein, term in egg:
        covered = closure.get(protein)
        if covered is None:
            novel.append((protein, term))
            continue
        # covered holds every ancestor of every InterProScan term on this
        # protein, so `term in covered` means the eggNOG term sits at or above
        # an InterProScan term. The reverse direction is an InterProScan term
        # at or below the eggNOG term.
        term_ancestors = ancestors(term, parents, cache)
        if term in covered or any(t in term_ancestors for t in ipr_by_protein[protein]):
            continue
        novel.append((protein, term))

    egg_proteins = {p for p, _ in egg}
    ipr_proteins = set(ipr_by_protein)
    egg_terms = {g for _, g in egg}
    specific = [(p, g) for p, g in novel if depth.get(g, 0) >= SPECIFIC_DEPTH]
    shared = egg_proteins & ipr_proteins
    gained = {p for p, _ in specific if p in shared}

    stats = {
        "eggnog_valid_associations": len(egg),
        "eggnog_proteins": len(egg_proteins),
        "eggnog_unique_terms": len(egg_terms),
        "interproscan_valid_associations": len(ipr),
        "interproscan_proteins": len(ipr_proteins),
        "interproscan_unique_terms": len({g for _, g in ipr}),
        "eggnog_proteins_also_in_interproscan": len(shared),
        "eggnog_only_proteins": len(egg_proteins - ipr_proteins),
        "exact_pair_overlap": len(exact),
        "closure_covered_associations": len(egg) - len(novel),
        "eggnog_only_associations": len(novel),
        f"eggnog_only_specific_depth{SPECIFIC_DEPTH}": len(specific),
        "eggnog_only_specific_proteins": len({p for p, _ in specific}),
        "eggnog_only_specific_terms": len({g for _, g in specific}),
        "shared_proteins_gaining_specific_term": len(gained),
        "shared_proteins_gaining_nothing_specific": len(shared) - len(gained),
    }

    width = max(len(k) for k in stats)
    for key, value in stats.items():
        print(f"{key.ljust(width)}  {value:>8}")
    if egg:
        print(f"\nexact overlap                {100 * len(exact) / len(egg):.1f}% of eggNOG associations")
        print(f"covered under ancestor closure {100 * (len(egg) - len(novel)) / len(egg):.1f}%")
        print(f"eggNOG-only                    {100 * len(novel) / len(egg):.1f}%")
        print(f"eggNOG-only and specific       {100 * len(specific) / len(egg):.1f}%")

    counts: dict[str, int] = defaultdict(int)
    for _, term in specific:
        counts[term] += 1
    print(f"\nMost frequent eggNOG-only terms at depth >= {SPECIFIC_DEPTH}")
    for term, count in sorted(counts.items(), key=lambda kv: -kv[1])[:20]:
        print(f"  {term}  d={depth.get(term, '?'):<3} {count:>4}  {names.get(term, '?')}")

    if args.out:
        summary = args.out.with_suffix(".tsv")
        summary.parent.mkdir(parents=True, exist_ok=True)
        summary.write_text(
            "metric\tvalue\n" + "".join(f"{k}\t{v}\n" for k, v in stats.items()),
            encoding="utf-8",
        )
        terms_path = args.out.parent / (args.out.name + "_eggnog_only_terms.tsv")
        terms_path.write_text(
            "go_id\tdepth\tproteins\tterm_name\n"
            + "".join(
                f"{t}\t{depth.get(t, '')}\t{c}\t{names.get(t, '')}\n"
                for t, c in sorted(counts.items(), key=lambda kv: -kv[1])
            ),
            encoding="utf-8",
        )
        print(f"\nwrote {summary}\nwrote {terms_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
