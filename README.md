# ProkaryoteAssembly

Two simple scripts to assemble prokaryotic genomes using paired-end reads.+

The first script, `assemble.py`, operates on a single sample at a time.

```bash
Usage: assemble.py [OPTIONS]

Options:
  -1, --fwd_reads PATH  Path to forward reads (R1).
  -2, --rev_reads PATH  Path to reverse reads (R2).
  -o, --out_dir PATH    Root directory to store all output files  [required]
  --version             Specify this flag to print the version and exit.
  --help                Show this message and exit.
```

The second script, `assemble_dir.py`, will detect all *.fastq.gz files in
a directory and run the assembly pipeline on each sample it can pair.

```bash
Usage: assemble_dir.py [OPTIONS]

Options:
  -i, --input_dir PATH  Directory containing all *.fastq.gz files to assemble.
                        [required]
  -o, --out_dir PATH    Root directory to store all output files.  [required]
  -f, --fwd_id TEXT     Pattern to detect forward reads. Defaults to "_R1".
  -r, --rev_id TEXT     Pattern to detect reverse reads. Defaults to "_R2".
  --help                Show this message and exit.

```

### Python (3.6) Dependencies
- click

### External Dependencies
**NOTE:** All external dependencies must be available via PATH.

*Versions confirmed to work are in brackets.*
- [skesa](https://github.com/ncbi/SKESA) (SKESA v.2.1-SVN_551987:557549M)
- [BBMap](https://sourceforge.net/projects/bbmap/) (BBMap version 38.22)
- [pilon](https://github.com/broadinstitute/pilon/wiki) (Pilon version 1.22)
- [samtools](http://www.htslib.org/download/) (samtools 1.8 using htslib 1.8)