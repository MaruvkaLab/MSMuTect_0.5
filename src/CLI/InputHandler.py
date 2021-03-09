import argparse, sys, os


def create_parser() -> argparse.ArgumentParser:
    # :return: creates parser with all command line arguments arguments
    MSMuTect_intro = "MSMuTect\n Version 3.2\n Authors: Avraham Kahan, Gaia Frant, and Yossi Maruvka"
    parser = argparse.ArgumentParser(description=MSMuTect_intro)
    parser.add_argument("-T", "--tumor_file", help="Tumor BAM file")
    parser.add_argument("-N", "--normal_file", help="Non-tumor BAM file")
    parser.add_argument("-S", "--single_file", help="Analyze a single file for histogram and/or alleles", action='store_true')
    parser.add_argument("-l", "--loci_file", help="File of loci to be processed and included in the output", required=True)
    parser.add_argument("-O", "--output_prefix", help="prefix for all output files", required=True)
    parser.add_argument("-c", "--cores", help="Number of cores to run MSMuTect on")
    parser.add_argument("-b", "--batch_start", help="1-indexed number locus to begin analyzing at (Inclusive)", default=1)
    parser.add_argument("-B", "--batch_end", help="1-indexed number locus to stop analyzing at (Inclusive)", default=-1)
    parser.add_argument("-H", "--histogram", help="Output a Histogram File", action='store_true')
    parser.add_argument("-A", "--allele", help="Output allele file", action='store_true')
    parser.add_argument("-m", "--mutation", help="Output mutation file", action='store_true')
    parser.add_argument("-f", "--flanking", help="Length of flanking on both sides of an accepted read", default=10)
    parser.add_argument("-r", "--removed_bases", help="Number of bases to be removed at the end of the read.", default=0)
    parser.add_argument("-e", "--exclude", help="The probability that a read will be randomly excluded while processing loci", default=0)
    parser.add_argument("-h", "--help", help="help", action='store_true')

    return parser


def exit_on(message: str, status: int = 1):
    # print message, and exit
    print(message)
    sys.exit(status)

def validate_bams(arguments: argparse.Namespace):
    if not ((bool(arguments.tumor_file) and bool(arguments.normal_file)) != bool(arguments.single_file)): #  XOR
        exit_on("Provide Single file, or both Normal and Tumor file")
    elif arguments.single_file:
        if not os.path.exists(arguments.single_file):
            exit_on("Provided single file path does not exist")
    else:
        if not os.path.exists(arguments.tumor_file) or not os.path.exists(arguments.normal_file):
            exit_on("Provided Normal or Tumor BAM path does not exist")


def validate_input(arguments: argparse.Namespace):
    if arguments.help():
        create_parser().print_help()
        sys.exit(0)
    elif not os.path.exists(arguments.loci_file):
        exit_on("Provided loci file does not exist")
    elif arguments.batch_start <= 0:
        exit_on("Batch Start must be equal to or greater than 1")
    elif arguments.cores <= 0:
        exit_on("Cores must be equal to or greater than 1")
    elif not os.path.exists(arguments.loci_file):
        exit_on("Loci file path does not exist")
