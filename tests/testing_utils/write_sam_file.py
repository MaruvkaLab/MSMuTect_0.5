import shutil, os
from typing import List
from collections import namedtuple

from tests.testing_utils.self_contained_utils import sample_bams_path, header_only_sam

FakeRead = namedtuple("FakeRead", field_names=["read_start", "cigar_str"])


def old():
    rl = create_readline(fake_reads=[
        FakeRead(9_954, "101M"),
        FakeRead(9_964, "101M"),
        FakeRead(10_035, "101M"),
        FakeRead(10_036, "101M"),
    ])
    add_to_end_of_file("/home/avraham/MaruvkaLab/msmutect_runs/data/fake/map.sam", rl)


def create_readline_custom_length(fake_reads: List[FakeRead], custom_length: int):
    if len(fake_reads) == 0:
        return

    seq = 'A' * custom_length
    # based on real TCGA case, but fields obscured and changed
    fields = ["FAKE",  # name
              '2', # bitwise flags. 2 indicates aligned properly
              '1', # chromosome
              '10051',  # start
              '4',  # mapping quality
              '101M',  # cigar
              '=', # reference name of next read
              '44444', # position of next read
              '108', # template length
              seq,
              seq,
              'X0:i:100',
              'MD:Z:79A22',
              'RG:Z:0.3',
              'XG:i:0',
              'AM:i:0',
              'NM:i:1',
              'SM:i:0',
              'XM:i:1',
              'XO:i:0',
              'MQ:i:0',
              'OQ:Z:C@SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS?A=A;ABB((,:9<??BBB@D9<A?B99AB',
              "XT:A:R"]


    all_new_reads = []
    for fr in fake_reads:
        new_read = fields.copy()
        new_read[3] = str(fr.read_start)
        new_read[5] = fr.cigar_str
        all_new_reads.append(new_read)
    return "\n".join(["\t".join(a) for a in all_new_reads])


def create_readline(fake_reads: List[FakeRead]):
    if len(fake_reads) == 0:
        return

    # based on real TCGA case, but fields obscured and changed
    fields = ["FAKE",  # name
              '2', # bitwise flags. 2 indicates aligned properly
              '1', # chromosome
              '10051',  # start
              '4',  # mapping quality
              '101M',  # cigar
              '=', # reference name of next read
              '44444', # position of next read
              '108', # template length
              'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
              'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
              'X0:i:100',
              'MD:Z:79A22',
              'RG:Z:0.3',
              'XG:i:0',
              'AM:i:0',
              'NM:i:1',
              'SM:i:0',
              'XM:i:1',
              'XO:i:0',
              'MQ:i:0',
              'OQ:Z:C@SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS?A=A;ABB((,:9<??BBB@D9<A?B99AB',
              "XT:A:R"]


    all_new_reads = []
    for fr in fake_reads:
        new_read = fields.copy()
        new_read[3] = str(fr.read_start)
        new_read[5] = fr.cigar_str
        all_new_reads.append(new_read)
    return "\n".join(["\t".join(a) for a in all_new_reads])


def add_to_end_of_file(fp: str, lines: str):
    with open(fp, 'a') as sam:
        sam.write(lines)


def create_new_bam_custom_length(new_name: str, fake_reads: List[FakeRead], custom_length: int):
    header_only_file = header_only_sam()
    new_filename = os.path.join(sample_bams_path(), new_name + ".sam")
    shutil.copyfile(header_only_file, new_filename)
    readlines = create_readline_custom_length(fake_reads, custom_length)
    add_to_end_of_file(new_filename, readlines)
    bam_filename = new_filename[:-4]+".bam"
    os.system(f"samtools view -b -h {new_filename} > {bam_filename}")
    os.system(f"samtools index {bam_filename}")


def create_new_bam(new_name: str, fake_reads: List[FakeRead]):
    header_only_file = header_only_sam()
    new_filename = os.path.join(sample_bams_path(), new_name + ".sam")
    shutil.copyfile(header_only_file, new_filename)
    readlines = create_readline(fake_reads)
    add_to_end_of_file(new_filename, readlines)
    bam_filename = new_filename[:-4]+".bam"
    os.system(f"samtools view -b -h {new_filename} > {bam_filename}")
    os.system(f"samtools index {bam_filename}")


create_new_bam("mapping_small_locus", [
        FakeRead(9_964, "101M"),  # shouldn't map (misses on flanking)
        FakeRead(9_965, "101M"),  # should map
        FakeRead(10_035, "101M"),  # should map
        FakeRead(10_036, "101M"),  # shouldn't map
])


create_new_bam("indels", [
        FakeRead(10_000, "35M30D66M"),  # knock out entire smallest locus. repeat_length=0

        FakeRead(10_035, "18M2D83M"),  # knock out end of smallest locus, repeat_length=9
        FakeRead(10_035, "19M10D82M"),  # knock out end and then some of smallest locus, repeat_length=9
        FakeRead(10_035, "19M3D82M"),  # knock out end and then some of smallest locus, repeat_length=9
        FakeRead(10_035, "9M3D92M"),  # knock out start of smallest locus, repeat_length=9

        FakeRead(10_035, "10M1D91M"),  # knock out start of smallest locus, repeat_length=10
        FakeRead(10_035, "10M1D91M"),  # knock out start of smallest locus, repeat_length=10


        FakeRead(10_035, "10M1I90M"),  # insertion at start of smallest locus, repeat_length=12
        FakeRead(10_035, "20M1I80M"),  # insertion at end of smallest locus, repeat_length=12
        FakeRead(10_035, "15M1I85M"),  # insertion of middle of smallest locus, repeat_length=12


        FakeRead(10_035, "5M1I95M"),  # insertion before start of smallest locus, repeat_length=11
        FakeRead(10_035, "40M2D61M"),  # deletion after end of smallest locus, repeat_length=11
        FakeRead(10_035, "101M"),   # standard: rl=11
        FakeRead(10_035, "101M"),  # standard: rl=11
        FakeRead(10_035, "101M"),   # standard: rl=11
        FakeRead(10_035, "101M"),   # standard: rl=11

    # 11_6, 9_4, 12_3, 10_2, 0_1
])


create_new_bam_custom_length("multimapping_loci", [
        FakeRead(9990, "150M"),  # should align to all
        FakeRead(9991, "150M"), # should align to all except biggest
        FakeRead(10_001, "150M"), # should align to all except biggest
        FakeRead(10_026, "150M"), # should align to first and third
        FakeRead(10_040, "150M") # should not align to any
], 150)