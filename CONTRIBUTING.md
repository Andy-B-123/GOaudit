# Contributing to GOaudit

GOaudit is intentionally small. Contributions should preserve its central
contract: a strict protein–GO table plus one NCBI taxid produces transparent,
reproducible association-level decisions.

## Report a problem

Open a GitHub issue with:

- the GOaudit version (`goaudit --version`);
- the command used, target taxid and operating system;
- the GO and NCBI reference manifest from the result directory;
- the smallest non-sensitive two-column input that reproduces the problem; and
- the complete error message or unexpected audit row.

Do not attach genome-scale inputs. Link to a stable public accession or provide
a minimal example instead.

## Make a change

```bash
git clone https://github.com/Andy-B-123/GOaudit.git
cd GOaudit
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
PYTHONPATH=src python -m unittest discover -s tests -v
```

Create a topic branch, add a focused test for behavioural changes, and open a
pull request. Network-dependent reference updates are intentionally excluded
from the unit test suite.

By contributing, you agree that your contribution is licensed under the
repository's MIT License.
