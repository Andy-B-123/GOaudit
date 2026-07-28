#!/usr/bin/env Rscript

# Build an AnnotationForge OrgDb from `goaudit prepare-orgdb` output.
# Usage:
# Rscript scripts/build_orgdb.R INPUT_DIR OUTPUT_DIR TAXID GENUS SPECIES VERSION "Name <email>"

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 7L) {
  stop(
    "Usage: build_orgdb.R INPUT_DIR OUTPUT_DIR TAXID GENUS SPECIES VERSION MAINTAINER\n",
    "Example: build_orgdb.R orgdb_inputs . 50429 Stylophora pistillata 0.1.0 ",
    "'Andreas Bachler <Andy.Bachler@csiro.au>'"
  )
}

input_dir <- args[[1L]]
output_dir <- args[[2L]]
tax_id <- args[[3L]]
genus <- args[[4L]]
species <- args[[5L]]
version <- args[[6L]]
maintainer <- args[[7L]]

if (!requireNamespace("AnnotationForge", quietly = TRUE)) {
  stop("Bioconductor package 'AnnotationForge' is required")
}
if (!requireNamespace("AnnotationDbi", quietly = TRUE) ||
    !requireNamespace("GO.db", quietly = TRUE) ||
    !requireNamespace("BiocManager", quietly = TRUE)) {
  stop("Bioconductor packages 'AnnotationDbi', 'GO.db', and 'BiocManager' are required")
}

read_input <- function(filename, required_columns) {
  path <- file.path(input_dir, filename)
  if (!file.exists(path)) stop("Missing GOaudit OrgDb input: ", path)
  value <- utils::read.delim(path, check.names = FALSE, stringsAsFactors = FALSE)
  missing <- setdiff(required_columns, names(value))
  if (length(missing)) {
    stop(filename, " is missing columns: ", paste(missing, collapse = ", "))
  }
  value[, required_columns, drop = FALSE]
}

gene_info <- read_input("gene_info.tsv", c("GID", "SYMBOL", "GENENAME"))
chromosome <- read_input("chromosome.tsv", c("GID", "CHROMOSOME"))
go <- read_input("go.tsv", c("GID", "GO", "EVIDENCE"))

if (anyDuplicated(gene_info$GID)) stop("gene_info.tsv contains duplicated GID values")
if (any(!chromosome$GID %in% gene_info$GID)) stop("chromosome.tsv contains unknown GID values")
if (any(!go$GID %in% gene_info$GID)) stop("go.tsv contains unknown GID values")
if (any(!grepl("^GO:[0-9]{7}$", go$GO))) stop("go.tsv contains malformed GO IDs")
if (!nrow(go)) stop("go.tsv is empty")
if (anyDuplicated(go)) stop("go.tsv contains duplicated rows")

dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

# AnnotationForge expands GO ancestors using the installed GO.db. GO releases
# can move slightly ahead of Bioconductor's GO.db, so make any dropped rows
# explicit instead of relying on AnnotationForge's otherwise terse warning.
go_db_ids <- AnnotationDbi::keys(GO.db::GO.db, keytype = "GOID")
go_not_in_go_db <- go[!go$GO %in% go_db_ids, , drop = FALSE]
if (nrow(go_not_in_go_db)) {
  mismatch_path <- file.path(output_dir, "go_not_in_GO_db.tsv")
  utils::write.table(
    go_not_in_go_db, mismatch_path, sep = "\t", row.names = FALSE, quote = FALSE
  )
  warning(
    nrow(go_not_in_go_db), " gene-GO rows use ",
    length(unique(go_not_in_go_db$GO)),
    " GO IDs absent from GO.db ", as.character(utils::packageVersion("GO.db")),
    "; excluded and recorded in ", mismatch_path
  )
  go <- go[go$GO %in% go_db_ids, , drop = FALSE]
}
if (!nrow(go)) stop("No GO rows remain after compatibility checking against GO.db")

build_manifest <- data.frame(
  field = c(
    "built_at", "taxid", "organism", "package_version", "R_version",
    "Bioconductor_version", "AnnotationForge_version", "AnnotationDbi_version",
    "GO_db_version", "gene_rows", "gene_GO_rows", "GO_db_mismatch_rows"
  ),
  value = c(
    format(Sys.time(), tz = "UTC", usetz = TRUE), tax_id,
    paste(genus, species), version, R.version.string,
    as.character(BiocManager::version()),
    as.character(utils::packageVersion("AnnotationForge")),
    as.character(utils::packageVersion("AnnotationDbi")),
    as.character(utils::packageVersion("GO.db")),
    nrow(gene_info), nrow(go), nrow(go_not_in_go_db)
  ),
  stringsAsFactors = FALSE
)
manifest_path <- file.path(output_dir, "orgdb_build_manifest.tsv")
utils::write.table(build_manifest, manifest_path, sep = "\t", row.names = FALSE, quote = FALSE)

package_path <- AnnotationForge::makeOrgPackage(
  gene_info = gene_info,
  chromosome = chromosome,
  go = go,
  version = version,
  maintainer = maintainer,
  author = maintainer,
  outputDir = output_dir,
  tax_id = tax_id,
  genus = genus,
  species = species,
  goTable = "go"
)

if (dir.exists(package_path)) {
  file.copy(manifest_path, file.path(package_path, "inst", "extdata"), overwrite = TRUE)
  if (nrow(go_not_in_go_db)) {
    file.copy(
      file.path(output_dir, "go_not_in_GO_db.tsv"),
      file.path(package_path, "inst", "extdata"), overwrite = TRUE
    )
  }
}
message("OrgDb source package created under: ", normalizePath(package_path))
