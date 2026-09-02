#!/usr/bin/env python3
"""
Extract Viral Reads from Kraken2 Output
========================================
This script extracts all reads classified as human viruses by Kraken2.

Usage:
    # Paired-end:
    python3 extract_viral_reads.py \
        --kraken_output YOUR_SAMPLE_output.txt \
        --r1 YOUR_SAMPLE_1.fastq.gz \
        --r2 YOUR_SAMPLE_2.fastq.gz \
        --sample_name YOUR_SAMPLE \
        --out_dir viral_reads_output/

    # Single-end:
    python3 extract_viral_reads.py \
        --kraken_output YOUR_SAMPLE_output.txt \
        --r1 YOUR_SAMPLE.fastq.gz \
        --sample_name YOUR_SAMPLE \
        --out_dir viral_reads_output/

WHAT TO CHANGE:
    --kraken_output : path to your Kraken2 _output.txt file
    --r1            : path to your R1 fastq.gz file
    --r2            : path to your R2 fastq.gz file (paired-end only)
    --sample_name   : your sample name (used for output file names)
    --out_dir       : where to save extracted reads (default: viral_reads_output)

Output files saved in viral_reads_output/YOUR_SAMPLE/:
    ALL_viral_R1.fastq.gz       <- all viral reads combined R1
    ALL_viral_R2.fastq.gz       <- all viral reads combined R2 (paired only)
    VZV_reads_R1.fastq.gz       <- VZV reads only
    CMV_reads_R1.fastq.gz       <- CMV reads only
    HSV1_reads_R1.fastq.gz      <- HSV-1 reads only
    HHV6A_reads_R1.fastq.gz     <- HHV-6A reads only
    ... one file per virus detected
    extraction_summary.txt      <- summary of how many reads extracted

SEND US:
    1. All files in viral_reads_output/YOUR_SAMPLE/ folder
    2. Your _report.txt file

Requirements:
    Python 3.6+ (no extra packages needed — uses built-in gzip only)

Author: Adarsh Agrawal
Institute: Helmholtz Institute for Infection Research (HZI)
Date: August 2026
"""

import os
import gzip
import argparse
from collections import defaultdict

# =============================================================================
# VIRUS TAXON IDs — DO NOT CHANGE
# =============================================================================
VIRUS_TAXIDS = {
    10335:   'VZV',
    10359:   'CMV',
    10298:   'HSV1',
    10310:   'HSV2',
    32603:   'HHV6A',
    12509:   'EBV',
    129951:  'Adenovirus_C',
    11676:   'HIV1',
    518987:  'Influenza_B',
    335341:  'Flu_A_H3N2',
    641809:  'Flu_A_H1N1',
    2697049: 'SARS_CoV2',
    138950:  'Poliovirus',
    11234:   'Measles',
    2560602: 'Mumps',
    11292:   'Rabies',
    138948:  'Enterovirus_A',
}

# =============================================================================
# STEP 1 — Read Kraken2 output and find viral read IDs
# =============================================================================
def get_viral_read_ids(kraken_output_file):
    print(f"Reading Kraken2 output: {kraken_output_file}")
    viral_reads  = {}
    total_reads  = 0
    virus_counts = defaultdict(int)

    with open(kraken_output_file) as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 3:
                continue
            total_reads += 1
            status  = parts[0]
            read_id = parts[1]
            try:
                taxid = int(parts[2])
            except:
                continue
            if status == 'C' and taxid in VIRUS_TAXIDS:
                clean_id = read_id.replace('/1','').replace('/2','').strip()
                viral_reads[clean_id]  = taxid
                virus_counts[VIRUS_TAXIDS[taxid]] += 1

    print(f"  Total reads scanned:  {total_reads:,}")
    print(f"  Viral reads found:    {len(viral_reads):,}")
    print("")
    print("  Reads per virus:")
    for virus, count in sorted(virus_counts.items(),
                                key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"    {virus:<22}: {count:,}")
    print("")
    return viral_reads, virus_counts

# =============================================================================
# STEP 2 — Extract matching reads from FASTQ file
# =============================================================================
def extract_reads(fastq_file, viral_read_ids):
    reads  = {}
    opener = gzip.open if fastq_file.endswith('.gz') else open
    mode   = 'rt'

    print(f"  Scanning: {os.path.basename(fastq_file)}")
    with opener(fastq_file, mode) as f:
        while True:
            header = f.readline().strip()
            seq    = f.readline().strip()
            plus   = f.readline().strip()
            qual   = f.readline().strip()
            if not header:
                break
            clean_id = header.replace('@','').split()[0]\
                             .replace('/1','').replace('/2','').strip()
            if clean_id in viral_read_ids:
                reads[clean_id] = (header, seq, qual)

    print(f"    Extracted: {len(reads):,} reads")
    return reads

# =============================================================================
# STEP 3 — Write extracted reads to gzipped FASTQ files
# =============================================================================
def write_fastq(reads_dict, viral_read_ids, filter_taxid, out_file):
    written = 0
    with gzip.open(out_file, 'wt') as f:
        for clean_id, (header, seq, qual) in reads_dict.items():
            taxid = viral_read_ids.get(clean_id)
            if filter_taxid is None or taxid == filter_taxid:
                f.write(f"{header}\n{seq}\n+\n{qual}\n")
                written += 1
    return written

# =============================================================================
# MAIN
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description='Extract viral reads from Kraken2 output',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--kraken_output', required=True,
                        help='Kraken2 _output.txt file')
    parser.add_argument('--r1', required=True,
                        help='R1 FASTQ file (or single-end)')
    parser.add_argument('--r2', default=None,
                        help='R2 FASTQ file (paired-end only)')
    parser.add_argument('--sample_name', required=True,
                        help='Your sample name')
    parser.add_argument('--out_dir', default='viral_reads_output',
                        help='Output directory (default: viral_reads_output)')
    args = parser.parse_args()

    out_dir = os.path.join(args.out_dir, args.sample_name)
    os.makedirs(out_dir, exist_ok=True)

    print("=" * 60)
    print(f"  EXTRACTING VIRAL READS — {args.sample_name}")
    print("=" * 60)
    print("")

    # Step 1: Get viral read IDs
    viral_read_ids, virus_counts = get_viral_read_ids(args.kraken_output)

    if not viral_read_ids:
        print("No viral reads found. Check your Kraken2 output file.")
        return

    # Step 2: Extract reads from FASTQ
    print("Extracting from FASTQ files...")
    r1_reads = extract_reads(args.r1, viral_read_ids)
    r2_reads = {}
    if args.r2:
        r2_reads = extract_reads(args.r2, viral_read_ids)

    # Step 3: Write output files
    print("")
    print("Writing output files...")
    summary = []

    # All viral reads combined
    out_r1_all = os.path.join(out_dir, 'ALL_viral_R1.fastq.gz')
    n1 = write_fastq(r1_reads, viral_read_ids, None, out_r1_all)
    print(f"  ALL R1: {n1:,} reads → {os.path.basename(out_r1_all)}")
    summary.append(('ALL viruses', n1))

    if args.r2 and r2_reads:
        out_r2_all = os.path.join(out_dir, 'ALL_viral_R2.fastq.gz')
        n2 = write_fastq(r2_reads, viral_read_ids, None, out_r2_all)
        print(f"  ALL R2: {n2:,} reads → {os.path.basename(out_r2_all)}")

    # Per-virus files
    for taxid, virus_name in VIRUS_TAXIDS.items():
        if virus_counts.get(virus_name, 0) == 0:
            continue

        out_r1 = os.path.join(out_dir, f'{virus_name}_reads_R1.fastq.gz')
        n1 = write_fastq(r1_reads, viral_read_ids, taxid, out_r1)

        if args.r2 and r2_reads:
            out_r2 = os.path.join(out_dir,
                                   f'{virus_name}_reads_R2.fastq.gz')
            write_fastq(r2_reads, viral_read_ids, taxid, out_r2)

        print(f"  {virus_name:<20}: {n1:,} reads → "
              f"{os.path.basename(out_r1)}")
        summary.append((virus_name, n1))

    # Write summary
    summary_file = os.path.join(out_dir, 'extraction_summary.txt')
    with open(summary_file, 'w') as f:
        f.write("VIRAL READ EXTRACTION SUMMARY\n")
        f.write("=" * 50 + "\n")
        f.write(f"Sample:          {args.sample_name}\n")
        f.write(f"Kraken2 output:  {args.kraken_output}\n")
        f.write(f"R1 input:        {args.r1}\n")
        if args.r2:
            f.write(f"R2 input:        {args.r2}\n")
        f.write("\n")
        f.write(f"{'Virus':<25} {'Reads extracted':>16}\n")
        f.write("-" * 45 + "\n")
        for virus, count in summary:
            f.write(f"{virus:<25} {count:>16,}\n")
        f.write("\n")
        f.write("PLEASE SEND TO US:\n")
        f.write("  1. All files in this folder\n")
        f.write("  2. Your _report.txt file\n")

    print("")
    print("=" * 60)
    print("  ALL DONE")
    print(f"  Output: {out_dir}/")
    print("=" * 60)
    print("")
    print("PLEASE SEND US:")
    print(f"  1. All files in: {out_dir}/")
    print(f"  2. Your _report.txt file")

if __name__ == '__main__':
    main()
