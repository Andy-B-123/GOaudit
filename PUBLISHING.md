# Publishing GOaudit

These instructions are for the maintainer. They deliberately separate the
small software release from genome-scale benchmark data.

## One-time GitHub setup

1. Create a new **empty** public repository named `GOaudit` under the
   `Andy-B-123` account. Do not initialise it with a README, `.gitignore` or
   licence because all three already exist locally.
2. Point the local remote at the new repository:

   ```bash
   git remote set-url origin https://github.com/Andy-B-123/GOaudit.git
   git remote -v
   ```

3. Confirm that `main` is checked out and run the checks below. This checkout
   retains the original data-bearing history only on the local
   `legacy-data-history` backup branch. Never push that backup branch.

## Pre-release checks

From the repository root:

```bash
git status --short
PYTHONPATH=src python -m unittest discover -s tests -v

python -m venv /tmp/goaudit-release
/tmp/goaudit-release/bin/python -m pip install .
/tmp/goaudit-release/bin/goaudit --version

python -m build
python -m twine check dist/*
```

The final two commands require the maintainer tools:

```bash
python -m pip install build twine
```

Check the current tree and the complete branch history for oversized files:

```bash
find . -path ./.git -prune -o -type f -size +10M -print
git rev-list --objects HEAD |
  git cat-file --batch-check='%(objecttype) %(objectsize) %(rest)' |
  awk '$1 == "blob" && $2 > 10000000 {print}'
```

Both commands should print nothing for the public branch. Never commit API
tokens, credentials, local environments, downloaded reference data, genome
files or complete annotation outputs.

## First public push

The clean public `main` branch has already been prepared. Upload only that
branch:

```bash
git switch main
git status --short
git push -u origin main
```

The upload is safe only when the history-size check above prints nothing. Do
not run `git push --all`, because that would also publish the local legacy
branch and its genome-scale blobs.

Future changes follow the usual Git workflow:

```bash
git add path/to/changed-file
git commit -m "Describe the change"
git push
```

## Tag a software release

After CI passes on `main`:

```bash
git tag -a v0.1.0 -m "GOaudit 0.1.0"
git push origin v0.1.0
```

On GitHub, choose **Releases → Draft a new release**, select `v0.1.0`, use the
matching section of `CHANGELOG.md` as release notes, and publish it. GitHub will
provide source `.zip` and `.tar.gz` archives automatically.

For a citable snapshot, connect the repository to Zenodo before publishing the
GitHub release. Add the resulting DOI to `CITATION.cff`, the README and the
manuscript.

## PyPI is a separate release

GitHub users can already install the package directly from the repository.
Publishing on PyPI is useful later because it enables `pip install goaudit`,
but it is not required for the first GitHub release. Reserve the project name,
configure PyPI trusted publishing, test on TestPyPI, and upload only the wheel
and source distribution in `dist/`—never any reference or benchmark data.
