# ProkaryoteAssembly

Two simple scripts to assemble prokaryotic genomes using paired-end reads.

## Pipeline Overview
1. QC on reads with bbduk.sh (adapter trimming/quality filtering)
2. Error-correction of reads with tadpole.sh
3. Assembly of reads with skesa
4. Alignment of error-corrected reads against draft assembly with bbmap.sh
5. Polishing of assembly with pilon

## Installation
```
pip install ProkaryoteAssembly
```

## Usage
The first script, `prokaryote_assemble.py`, operates on a single sample at a time.

```bash
Usage: prokaryote_assemble.py [OPTIONS]

Options:
  -1, --fwd_reads PATH  Path to forward reads (R1).  [required]
  -2, --rev_reads PATH  Path to reverse reads (R2).  [required]
  -o, --out_dir PATH    Root directory to store all output files.  [required]
  --cleanup             Specify this flag to remove everything except the final assembly upon completion.
  --version             Specify this flag to print the version and exit.
  --help                Show this message and exit.
```

The second script, `prokaryote_assemble_dir.py`, will detect all *.fastq.gz files in
a directory and run the assembly pipeline on each sample it can pair.

```bash
Usage: prokaryote_assemble_dir.py [OPTIONS]

Options:
  -i, --input_dir PATH  Directory containing all *.fastq.gz files to assemble.
                        [required]
  -o, --out_dir PATH    Root directory to store all output files.  [required]
  -f, --fwd_id TEXT     Pattern to detect forward reads. Defaults to "_R1".
  -r, --rev_id TEXT     Pattern to detect reverse reads. Defaults to "_R2".
  --cleanup             Specify this flag to remove everything except the final assembly upon completion.
  --help                Show this message and exit.

```

## Python (3.6) Dependencies
- click

## External Dependencies
**NOTE:** All external dependencies must be available via PATH.

*Versions confirmed to work are in brackets.*
- [skesa](https://github.com/ncbi/SKESA) (SKESA v.2.1-SVN_551987:557549M)
- [BBMap](https://sourceforge.net/projects/bbmap/) (BBMap version 38.22)
- [samtools](http://www.htslib.org/download/) (samtools 1.8 using htslib 1.8)
- [pilon](https://github.com/broadinstitute/pilon/wiki) (Pilon version 1.22)

*Note:*
Strongly recommend installing pilon via conda e.g.
https://bioconda.github.io/recipes/pilon/README.html
```
conda install pilon
```