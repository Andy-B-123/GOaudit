"""Load and update the official GO and NCBI data used by GOaudit."""

from __future__ import annotations

from array import array
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tarfile
import tempfile
from urllib.request import Request, urlopen


GO_ONTOLOGY_URL = "https://current.geneontology.org/ontology/go.obo"
GO_CONSTRAINTS_URL = (
    "https://current.geneontology.org/ontology/imports/"
    "go-computed-taxon-constraints.obo"
)
GO_GROUPINGS_URL = (
    "https://current.geneontology.org/ontology/imports/go-taxon-groupings.obo"
)
NCBI_TAXDUMP_URL = "https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz"
DATA_FILES = ("go.obo", "go-computed-taxon-constraints.obo", "go-taxon-groupings.obo", "nodes.dmp", "names.dmp", "merged.dmp")


def default_data_dir() -> Path:
    cache = os.environ.get("XDG_CACHE_HOME")
    return Path(cache).expanduser() / "goaudit" if cache else Path.home() / ".cache" / "goaudit"


@dataclass(frozen=True)
class GOTerm:
    go_id: str
    name: str
    namespace: str
    obsolete: bool = False
    replaced_by: tuple[str, ...] = ()


@dataclass
class Ontology:
    terms: dict[str, GOTerm] = field(default_factory=dict)
    alt_ids: dict[str, str] = field(default_factory=dict)
    data_version: str = "unknown"

    def resolve(self, go_id: str) -> tuple[str, GOTerm | None]:
        canonical = self.alt_ids.get(go_id, go_id)
        return canonical, self.terms.get(canonical)


@dataclass
class Constraints:
    in_taxon: dict[str, tuple[str, ...]] = field(default_factory=dict)
    never_in_taxon: dict[str, tuple[str, ...]] = field(default_factory=dict)


def _stanzas(path: Path):
    header: list[str] = []
    stanza: list[str] = []
    in_term = False
    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            line = raw.rstrip("\n")
            if line == "[Term]":
                if stanza:
                    yield stanza
                stanza = []
                in_term = True
            elif line.startswith("["):
                if stanza:
                    yield stanza
                stanza = []
                in_term = False
            elif in_term:
                if not line:
                    if stanza:
                        yield stanza
                    stanza = []
                    in_term = False
                else:
                    stanza.append(line)
            else:
                header.append(line)
        if stanza:
            yield stanza
    _stanzas.header = header


_stanzas.header = []


def load_ontology(path: Path) -> Ontology:
    ontology = Ontology()
    for lines in _stanzas(path):
        values: dict[str, list[str]] = {}
        for line in lines:
            if ": " in line:
                key, value = line.split(": ", 1)
                values.setdefault(key, []).append(value)
        ids = values.get("id", [])
        if not ids or not ids[0].startswith("GO:"):
            continue
        go_id = ids[0]
        term = GOTerm(
            go_id=go_id,
            name=values.get("name", [""])[0],
            namespace=values.get("namespace", ["unknown"])[0],
            obsolete=values.get("is_obsolete", ["false"])[0] == "true",
            replaced_by=tuple(v.split()[0] for v in values.get("replaced_by", [])),
        )
        ontology.terms[go_id] = term
        for alt_id in values.get("alt_id", []):
            ontology.alt_ids[alt_id.split()[0]] = go_id
    for line in _stanzas.header:
        if line.startswith("data-version: "):
            ontology.data_version = line.split(": ", 1)[1]
            break
    return ontology


def load_constraints(path: Path) -> Constraints:
    only: dict[str, list[str]] = {}
    never: dict[str, list[str]] = {}
    for lines in _stanzas(path):
        go_id = next((x[4:] for x in lines if x.startswith("id: GO:")), None)
        if not go_id:
            continue
        for line in lines:
            match = re.match(r"(?:relationship|property_value): (RO:\d+) (\S+)", line)
            if not match:
                continue
            relation, taxon = match.groups()
            if relation == "RO:0002162":
                only.setdefault(go_id, []).append(taxon)
            elif relation == "RO:0002161":
                never.setdefault(go_id, []).append(taxon)
    return Constraints(
        in_taxon={key: tuple(value) for key, value in only.items()},
        never_in_taxon={key: tuple(value) for key, value in never.items()},
    )


def load_groupings(path: Path) -> dict[str, tuple[int, ...]]:
    groups: dict[str, tuple[int, ...]] = {}
    for lines in _stanzas(path):
        term_id = next((x[4:] for x in lines if x.startswith("id: NCBITaxon_Union:")), None)
        if not term_id:
            continue
        members = []
        for line in lines:
            if line.startswith("union_of: NCBITaxon:"):
                members.append(int(line.split(":", 2)[2].split()[0]))
        groups[term_id] = tuple(members)
    return groups


class Taxonomy:
    """A memory-efficient NCBI taxonomy lineage reader."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.parents = array("I")
        with (data_dir / "nodes.dmp").open(encoding="ascii") as handle:
            for line in handle:
                fields = line.split("\t|\t", 2)
                taxid, parent = int(fields[0]), int(fields[1])
                if taxid >= len(self.parents):
                    self.parents.extend([0] * (taxid + 1 - len(self.parents)))
                self.parents[taxid] = parent
        self.merged: dict[int, int] = {}
        merged_path = data_dir / "merged.dmp"
        if merged_path.exists():
            with merged_path.open(encoding="ascii") as handle:
                for line in handle:
                    fields = [field.strip() for field in line.split("|")]
                    self.merged[int(fields[0])] = int(fields[1])

    def canonical(self, taxid: int) -> int:
        seen = set()
        while taxid in self.merged and taxid not in seen:
            seen.add(taxid)
            taxid = self.merged[taxid]
        return taxid

    def lineage(self, taxid: int) -> tuple[int, ...]:
        taxid = self.canonical(taxid)
        if taxid <= 0 or taxid >= len(self.parents) or self.parents[taxid] == 0:
            raise ValueError(f"Taxonomy ID {taxid} is not present in nodes.dmp")
        lineage: list[int] = []
        seen = set()
        current = taxid
        while current not in seen:
            lineage.append(current)
            seen.add(current)
            parent = self.parents[current]
            if parent == current:
                break
            current = parent
        return tuple(lineage)

    def names(self, taxids: set[int]) -> dict[int, str]:
        result: dict[int, str] = {}
        with (self.data_dir / "names.dmp").open(encoding="utf-8") as handle:
            for line in handle:
                fields = line.rstrip("\n").split("\t|\t")
                taxid = int(fields[0])
                if taxid in taxids and fields[3].rstrip("\t|") == "scientific name":
                    result[taxid] = fields[1]
                    if len(result) == len(taxids):
                        break
        return result


def ensure_data(data_dir: Path) -> None:
    missing = [name for name in DATA_FILES if not (data_dir / name).is_file()]
    if missing:
        joined = ", ".join(missing)
        raise FileNotFoundError(
            f"Missing reference data in {data_dir}: {joined}. Run 'goaudit update --data-dir {data_dir}'."
        )


def _download(url: str, destination: Path) -> None:
    request = Request(url, headers={"User-Agent": "GOaudit/0.1"})
    with urlopen(request, timeout=120) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def update_data(data_dir: Path) -> dict:
    """Atomically download current GO data and the NCBI taxdump."""
    data_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="goaudit-", dir=data_dir) as temporary:
        temp = Path(temporary)
        downloads = {
            "go.obo": GO_ONTOLOGY_URL,
            "go-computed-taxon-constraints.obo": GO_CONSTRAINTS_URL,
            "go-taxon-groupings.obo": GO_GROUPINGS_URL,
            "taxdump.tar.gz": NCBI_TAXDUMP_URL,
        }
        for name, url in downloads.items():
            _download(url, temp / name)
        with tarfile.open(temp / "taxdump.tar.gz", "r:gz") as archive:
            for name in ("nodes.dmp", "names.dmp", "merged.dmp"):
                member = archive.getmember(name)
                source = archive.extractfile(member)
                if source is None:
                    raise RuntimeError(f"NCBI taxdump is missing {name}")
                with (temp / name).open("wb") as output:
                    shutil.copyfileobj(source, output)
        manifest = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "sources": downloads,
            "sha256": {name: _sha256(temp / name) for name in DATA_FILES},
        }
        (temp / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        for name in (*DATA_FILES, "manifest.json"):
            os.replace(temp / name, data_dir / name)
    return manifest
