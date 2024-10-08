# cython: language_level=3
import os
from typing import List
from collections import namedtuple
from pysam import AlignmentFile

from src.IndelCalling.Locus import Locus
from src.IndelCalling.AlleleSet import AlleleSet
from src.IndelCalling.Histogram import Histogram
from src.IndelCalling.CallAlleles import calculate_alleles
from src.IndelCalling.CallMutations import call_mutations, is_possible_mutation
from src.IndelCalling.FisherTest import Fisher
from src.IndelCalling.MutationCall import MutationCall

from src.GenomicUtils.ReadsFetcher import ReadsFetcher
from src.GenomicUtils.LocusFile import LociManager
from src.GenomicUtils.NoiseTable import get_noise_table
from . import BatchUtil
from .FileBackedQueue import FileBackedQueue

PairResults = namedtuple("PairResults", ['normal_alleles', 'tumor_alleles', 'decision'])


def format_mutation_call(decision: MutationCall):
    return f"{str(decision.normal_alleles.histogram.locus)}\t{str(decision.normal_alleles.histogram)}\t{str(decision.normal_alleles)}\t{str(decision.tumor_alleles.histogram)}\t{str(decision.tumor_alleles)}\t{str(decision)}"


def run_full_pair(normal: str, tumor: str, loci_file: str, batch_start: int,
                       batch_end: int, cores: int, flanking: int, required_reads: int, integer_indels_only, output_prefix: str) -> str:
    # returns path of output file
    loci_iterator = LociManager(loci_file, batch_start)
    noise_table = get_noise_table()
    results: List[FileBackedQueue] = BatchUtil.run_batch(partial_full_pair, [normal, tumor, flanking, noise_table, required_reads, integer_indels_only], loci_iterator,
                                  (batch_end - batch_start), cores, os.path.dirname(output_prefix))
    mutation_header = f"{Locus.header()}\t{Histogram.header(prefix='NORMAL_')}\t{AlleleSet.header(prefix='NORMAL_')}\t{Histogram.header(prefix='TUMOR_')}\t{AlleleSet.header(prefix='TUMOR_')}\t{MutationCall.header()}"
    output_file = output_prefix + ".full.mut"
    BatchUtil.write_queues_results(output_file, results, mutation_header)
    return output_file+".tsv"


def get_alleles(locus: Locus, reads_fetcher: ReadsFetcher, flanking: int, noise_table, required_reads: int, integer_indels_only: bool) -> AlleleSet:
    histogram = Histogram(locus, integer_indels_only)
    reads = reads_fetcher.get_reads(locus.chromosome, locus.start - flanking, locus.end + flanking)
    histogram.add_reads(reads)
    alleles = calculate_alleles(histogram, noise_table, required_read_support=required_reads)
    return alleles


def partial_full_pair(loci: List[Locus], normal: str, tumor: str, flanking: int, noise_table, required_reads: int,
                      integer_indels_only: bool, results_dir: str) -> FileBackedQueue:
    calls = FileBackedQueue(out_file_dir=results_dir, max_memory=10**7)  # 10MB
    if len(loci) != 0:
        normal_fetcher = ReadsFetcher(AlignmentFile(normal, "rb"), loci[0].chromosome)
        tumor_fetcher = ReadsFetcher(AlignmentFile(tumor, "rb"), loci[0].chromosome)
        fisher = Fisher()
        for locus in loci:
            normal_alleles = get_alleles(locus, normal_fetcher, flanking, noise_table, required_reads, integer_indels_only)
            tumor_alleles = get_alleles(locus, tumor_fetcher, flanking, noise_table, required_reads, integer_indels_only)
            calls.append(format_mutation_call(call_mutations(normal_alleles, tumor_alleles, noise_table, fisher)))
    calls.close()
    return calls


def run_mutations_pair(normal: str, tumor: str, loci_file: str, batch_start: int,
                       batch_end: int, cores: int, flanking: int, required_reads: int, integer_indels_only: bool, output_prefix: str):
    # returns output file
    loci_iterator = LociManager(loci_file, batch_start)
    noise_table = get_noise_table()
    results: List[FileBackedQueue] = BatchUtil.run_batch(partial_mutations_pair, [normal, tumor, flanking, noise_table,
                                                                                  required_reads, integer_indels_only],
                                                     loci_iterator,
                                                     (batch_end - batch_start), cores, result_dir=os.path.dirname(output_prefix))
    mutation_header = f"{Locus.header()}\t{Histogram.header(prefix='NORMAL_')}\t{AlleleSet.header(prefix='NORMAL_')}\t{Histogram.header(prefix='TUMOR_')}\t{AlleleSet.header(prefix='TUMOR_')}\t{MutationCall.header()}"
    output_file = output_prefix + ".partial.mut"
    BatchUtil.write_queues_results(output_file, results, mutation_header)
    return output_file+".tsv"


def get_tumor_alleles(reads_fetcher: ReadsFetcher, locus: Locus, flanking: int, noise_table, required_reads=6, integer_indels_only=False) -> AlleleSet:
    histogram = Histogram(locus, integer_indels_only=integer_indels_only)
    reads = reads_fetcher.get_reads(locus.chromosome, locus.start - flanking, locus.end + flanking)
    histogram.add_reads(reads)
    current_alleles = calculate_alleles(histogram, noise_table, required_read_support=required_reads)
    return current_alleles


def partial_mutations_pair(loci: List[Locus], normal: str, tumor: str, flanking: int, noise_table, required_reads: int,
                           integer_indels_only: bool, results_dir: str) -> FileBackedQueue:
    calls = FileBackedQueue(out_file_dir=results_dir, max_memory=10**7) # 10MB
    if len(loci) != 0:
        normal_fetcher = ReadsFetcher(AlignmentFile(normal, "rb"), loci[0].chromosome)
        tumor_fetcher = ReadsFetcher(AlignmentFile(tumor, "rb"), loci[0].chromosome)
        fisher = Fisher()
        for locus in loci:
            normal_alleles = get_alleles(locus, normal_fetcher, flanking, noise_table, required_reads, integer_indels_only)
            if is_possible_mutation(normal_alleles):
                tumor_alleles = get_alleles(locus, tumor_fetcher, flanking, noise_table, required_reads, integer_indels_only)
                calls.append(format_mutation_call(call_mutations(normal_alleles, tumor_alleles, noise_table, fisher)))
    calls.close()
    return calls
