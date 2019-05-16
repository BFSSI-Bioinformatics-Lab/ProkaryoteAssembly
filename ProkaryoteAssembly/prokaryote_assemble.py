#!/usr/bin/env python3

import logging
import os
import shutil
from pathlib import Path

import click

from ProkaryoteAssembly.accessories import print_version, convert_to_path, run_subprocess, check_all_dependencies

script = os.path.basename(__file__)
logger = logging.getLogger()
logging.basicConfig(
    format=f'\033[92m \033[1m {script}:\033[0m %(message)s ',
    level=logging.INFO)


@click.command()
@click.option('-1', '--fwd_reads',
              type=click.Path(exists=True),
              required=True,
              help='Path to forward reads (R1) (gzipped FASTQ).',
              callback=convert_to_path)
@click.option('-2', '--rev_reads',
              type=click.Path(exists=True),
              required=True,
              help='Path to reverse reads (R2) (gzipped FASTQ).',
              callback=convert_to_path)
@click.option('-o', '--out_dir',
              type=click.Path(exists=False),
              required=True,
              help='Root directory to store all output files.',
              callback=convert_to_path)
@click.option('-m', '--memory',
              type=click.STRING,
              required=False,
              help='Memory to allocate to pilon call. Defaults to "8g" (i.e. pilon -Xmx8g). May need to provide a large'
                   ' amount of memory for large read sets/assemblies.',
              default='8g')
@click.option('--cleanup',
              help='Specify this flag to delete all intermediary files except the resulting FASTA assembly.',
              default=False,
              required=False,
              is_flag=True)
@click.option('--version',
              help='Specify this flag to print the version and exit.',
              is_flag=True,
              is_eager=True,
              callback=print_version,
              expose_value=False)
def assemble(fwd_reads, rev_reads, out_dir, memory, cleanup):
    check_all_dependencies()

    sample_id = get_id(fwd_reads=fwd_reads, rev_reads=rev_reads)
    logging.info(f"Starting ProkaryoteAssembly!")
    if out_dir.exists():
        logging.error(f"ERROR: Output directory {out_dir} already exists. Specify a directory that does not yet exist.")
        quit()
    else:
        out_dir.mkdir(parents=True)

    assembly_pipeline(fwd_reads=fwd_reads,
                      rev_reads=rev_reads,
                      out_dir=out_dir,
                      sample_id=sample_id,
                      memory=memory)

    if cleanup:
        total_cleanup(input_dir=out_dir)
    else:
        basic_cleanup(input_dir=out_dir)


def total_cleanup(input_dir: Path):
    all_files = list(input_dir.glob("*"))
    for f in all_files:
        if ".fasta" not in f.name:
            try:
                os.remove(str(f))
            except:
                pass
    try:
        shutil.rmtree(str(input_dir / 'pilon'))
    except FileNotFoundError:
        pass


def basic_cleanup(input_dir: Path):
    all_files = list(input_dir.glob("*"))
    for f in all_files:
        if ".filtered" in f.name:
            os.remove(str(f))
        elif ".contigs.bam" in f.name:
            os.remove(str(f))
        elif ".contigs.fa" in f.name:
            os.remove(str(f))
    try:
        shutil.rmtree(str(input_dir / 'pilon'))
    except FileNotFoundError:
        pass


def assembly_pipeline(fwd_reads: Path, rev_reads: Path, out_dir: Path, sample_id: str, memory: str = '8g'):
    fwd_reads, rev_reads = call_bbduk(fwd_reads=fwd_reads, rev_reads=rev_reads, out_dir=out_dir)
    fwd_reads, rev_reads = call_tadpole(fwd_reads=fwd_reads, rev_reads=rev_reads, out_dir=out_dir)
    assembly = call_skesa(fwd_reads=fwd_reads, rev_reads=rev_reads, out_dir=out_dir, sample_id=sample_id)
    bamfile = call_bbmap(fwd_reads=fwd_reads, rev_reads=rev_reads, out_dir=out_dir, assembly=assembly)
    polished_assembly = call_pilon(out_dir=out_dir, assembly=assembly, prefix=sample_id, bamfile=bamfile, memory=memory)
    shutil.move(src=str(polished_assembly), dst=str(out_dir / polished_assembly.name.replace(".fasta", ".pilon.fasta")))
    return polished_assembly


def get_id(fwd_reads: Path, rev_reads: Path) -> str:
    element_1 = fwd_reads.name.split("_")[0]
    element_2 = rev_reads.name.split("_")[0]
    if element_1 == element_2:
        logging.info(f"Set Sample ID to {element_1}")
        return element_1


def call_pilon(bamfile: Path, out_dir: Path, assembly: Path, prefix: str, memory: str) -> Path:
    out_dir = out_dir / 'pilon'
    os.makedirs(str(out_dir), exist_ok=True)
    cmd = f"pilon -Xmx{memory} --genome {assembly} --bam {bamfile} --outdir {out_dir} --output {prefix}"
    run_subprocess(cmd)
    polished_assembly = Path(list(out_dir.glob("*.fasta"))[0])
    return polished_assembly


def call_skesa(fwd_reads: Path, rev_reads: Path, out_dir: Path, sample_id: str) -> Path:
    assembly_out = out_dir / Path(sample_id + ".contigs.fa")

    if assembly_out.exists():
        return assembly_out

    cmd = f'skesa --use_paired_ends --gz --fastq "{fwd_reads},{rev_reads}" --contigs_out {assembly_out}'
    run_subprocess(cmd)
    return assembly_out


def index_bamfile(bamfile: Path):
    cmd = f"samtools index {bamfile}"
    run_subprocess(cmd)


def call_bbmap(fwd_reads: Path, rev_reads: Path, out_dir: Path, assembly: Path) -> Path:
    outbam = out_dir / assembly.with_suffix(".bam").name

    if outbam.exists():
        return outbam

    cmd = f"bbmap.sh in1={fwd_reads} in2={rev_reads} ref={assembly} out={outbam} overwrite=t deterministic=t " \
        f"bamscript=bs.sh; sh bs.sh"
    run_subprocess(cmd)

    sorted_bam_file = out_dir / outbam.name.replace(".bam", "_sorted.bam")
    index_bamfile(sorted_bam_file)
    return sorted_bam_file


def call_tadpole(fwd_reads: Path, rev_reads: Path, out_dir: Path) -> tuple:
    fwd_out = out_dir / fwd_reads.name.replace(".filtered.", ".corrected.")
    rev_out = out_dir / rev_reads.name.replace(".filtered.", ".corrected.")

    if fwd_out.exists() and rev_out.exists():
        return fwd_out, rev_out

    cmd = f"tadpole.sh in1={fwd_reads} in2={rev_reads} out1={fwd_out} out2={rev_out} mode=correct"
    run_subprocess(cmd)
    return fwd_out, rev_out


def call_bbduk(fwd_reads: Path, rev_reads: Path, out_dir: Path) -> tuple:
    fwd_out = out_dir / fwd_reads.name.replace(".fastq.gz", ".filtered.fastq.gz")
    rev_out = out_dir / rev_reads.name.replace(".fastq.gz", ".filtered.fastq.gz")

    if fwd_out.exists() and rev_out.exists():
        return fwd_out, rev_out

    cmd = f"bbduk.sh in1={fwd_reads} in2={rev_reads} out1={fwd_out} out2={rev_out} " \
        f"ref=adapters maq=12 qtrim=rl tpe tbo overwrite=t"
    run_subprocess(cmd)
    return fwd_out, rev_out


if __name__ == "__main__":
    assemble()
