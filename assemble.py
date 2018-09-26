import os
import click
import shutil
import logging
from pathlib import Path
from subprocess import Popen, PIPE

__version__ = "0.0.1"
__author__ = "Forest Dussault"
__email__ = "forest.dussault@canada.ca"

script = os.path.basename(__file__)
logger = logging.getLogger()
logging.basicConfig(
    format=f'\033[92m \033[1m {script}:\033[0m %(message)s ',
    level=logging.DEBUG)


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    logging.info(f"Version: {__version__}")
    logging.info(f"Author: {__author__}")
    logging.info(f"Email: {__email__}")
    quit()


def convert_to_path(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    return Path(value)


@click.command()
@click.option('-1', '--fwd_reads',
              type=click.Path(exists=True),
              required=False,
              default=None,
              help='Path to forward reads (R1). Only used for hybrid assembly.',
              callback=convert_to_path)
@click.option('-2', '--rev_reads',
              type=click.Path(exists=True),
              required=False,
              default=None,
              help='Path to reverse reads (R2). Only used for hybrid assembly.',
              callback=convert_to_path)
@click.option('-o', '--out_dir',
              type=click.Path(exists=False),
              required=True,
              help='Root directory to store all output files',
              callback=convert_to_path)
@click.option('--version',
              help='Specify this flag to print the version and exit.',
              is_flag=True,
              is_eager=True,
              callback=print_version,
              expose_value=False)
def assemble(fwd_reads, rev_reads, out_dir):
    sample_id = get_id(fwd_reads=fwd_reads, rev_reads=rev_reads)
    logging.info(f"Starting ProkaryoteAssembly!")
    assembly_pipeline(fwd_reads=fwd_reads,
                      rev_reads=rev_reads,
                      out_dir=out_dir,
                      sample_id=sample_id)
    clean_up(input_dir=out_dir)


def clean_up(input_dir: Path):
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


def assembly_pipeline(fwd_reads: Path, rev_reads: Path, out_dir: Path, sample_id: str):
    fwd_reads, rev_reads = call_bbduk(fwd_reads=fwd_reads, rev_reads=rev_reads, out_dir=out_dir)
    fwd_reads, rev_reads = call_tadpole(fwd_reads=fwd_reads, rev_reads=rev_reads, out_dir=out_dir)
    assembly = call_skesa(fwd_reads=fwd_reads, rev_reads=rev_reads, out_dir=out_dir, sample_id=sample_id)
    bamfile = call_bbmap(fwd_reads=fwd_reads, rev_reads=rev_reads, out_dir=out_dir, assembly=assembly)
    polished_assembly = call_pilon(out_dir=out_dir, assembly=assembly, prefix=sample_id, bamfile=bamfile)
    shutil.move(src=str(polished_assembly), dst=str(out_dir / polished_assembly.name.replace(".fasta", ".pilon.fasta")))
    return polished_assembly


def run_subprocess(cmd: str, get_stdout=False):
    if get_stdout:
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        out = out.decode().strip()
        err = err.decode().strip()
        if out != "":
            return out
        elif err != "":
            return err
        else:
            return ""
    else:
        p = Popen(cmd, shell=True)
        p.wait()


def get_id(fwd_reads: Path, rev_reads: Path) -> str:
    element_1 = fwd_reads.name.split("_")[0]
    element_2 = rev_reads.name.split("_")[0]
    if element_1 == element_2:
        logging.info(f"Set Sample ID to {element_1}")
        return element_1


def call_pilon(bamfile: Path, out_dir: Path, assembly: Path, prefix: str) -> Path:
    out_dir = out_dir / 'pilon'
    os.makedirs(str(out_dir), exist_ok=True)
    cmd = f"pilon -Xmx128g --genome {assembly} --bam {bamfile} --outdir {out_dir} --output {prefix}"
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

    cmd = f"bbmap.sh in1={fwd_reads} in2={rev_reads} ref={assembly} out={outbam} overwrite=t bamscript=bs.sh; sh bs.sh"
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
