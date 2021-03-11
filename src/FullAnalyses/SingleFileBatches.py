import multiprocessing
import numpy as np
from typing import List
from pysam import AlignmentFile
from collections import namedtuple
from multiprocessing import Pool

from src.BAMutil.ReadsFetcher import ReadsFetcher
from src.FullAnalyses.WriteResults import write_histograms, write_alleles
from src.SingleFileAnalysis.Histogram import Histogram
from src.SingleFileAnalysis.Locus import Locus
from src.SingleFileAnalysis.CalculateAlleles import calculate_alleles

Chunk = namedtuple("Chunk", ["start", "end"])

AllelicAnalysis = namedtuple("AllelicAnalysis", ['histogram', 'alleles'])  # container for analysis of histogram and alleles


def combine_results(results: List[multiprocessing.pool.ApplyResult[list]]) -> list:
    combined = []
    for result in results:
        combined += result.get()
    return combined


def get_chunks(cores: int, batch_start: int, batch_end: int) -> List[Chunk]:
    chunks = []
    batch_size = (batch_end - batch_start) // cores
    prev_end = batch_start - 1
    for i in range(cores-1):
        chunks.append(Chunk(start=prev_end + 1, end=prev_end + batch_size))
        prev_end += batch_size
    chunks.append(Chunk(start=prev_end + 1, end=batch_end))
    return chunks


def run_single_allelic(BAM: str, loci: List[Locus], batch_start: int,
                       batch_end: int, cores: int, flanking: int, output_prefix: str) -> None:
    BAM_handle = AlignmentFile(BAM, "rb")
    chunks = get_chunks(cores, batch_start, batch_end)
    results = []
    noise_table = np.loadtxt("", delimiter=',')  # noise table
    with Pool(processes=cores) as processes:
        for i in range(cores):
            results.append(processes.apply_async(partial_single_allelic,
                                                 args=(BAM_handle, loci, chunks[i].start, chunks[i].end, flanking, noise_table)))
        processes.close()
        processes.join()
    write_alleles(output_prefix, combine_results(results))


def partial_single_allelic(BAM_handle: AlignmentFile, loci: List[Locus], start: int, end: int, flanking: int, noise_table):
    allelic_results: List[AllelicAnalysis] = []
    reads_fetcher = ReadsFetcher(BAM_handle, loci[0].chromosome)
    for i in range(start, end):
        locus = loci[i]
        current_histogram = Histogram(locus)
        reads = reads_fetcher.get_reads(loci[i].chromosome, loci[i].start - flanking, loci[i].end + flanking)
        current_histogram.add_reads(reads)
        current_alleles = calculate_alleles(current_histogram, noise_table)
        allelic_results.append(AllelicAnalysis(histogram=current_histogram, alleles=current_alleles))
    return allelic_results


def run_single_histogram(BAM: str, loci: List[Locus], batch_start: int,
                         batch_end: int, cores: int, flanking: int, output_prefix: str) -> None:
    BAM_handle = AlignmentFile(BAM, "rb")
    chunks = get_chunks(cores, batch_start, batch_end)
    results = []
    with Pool(processes=cores) as processes:
        for i in range(cores):
            results.append(processes.apply_async(partial_single_histogram, args=(BAM_handle, loci, chunks[i].start, chunks[i].end, flanking)))
        processes.close()
        processes.join()
    write_histograms(output_prefix, combine_results(results))


def partial_single_histogram(BAM_handle: AlignmentFile, loci: List[Locus], start: int, end: int, flanking: int) -> List[Histogram]:
    histograms = []
    reads_fetcher = ReadsFetcher(BAM_handle, loci[0].chromosome)
    for i in range(start, end):
        locus = loci[i]
        current_histogram = Histogram(locus)
        reads = reads_fetcher.get_reads(loci[i].chromosome, loci[i].start - flanking, loci[i].end + flanking)
        current_histogram.add_reads(reads)
        histograms.append(current_histogram)
    return histograms
