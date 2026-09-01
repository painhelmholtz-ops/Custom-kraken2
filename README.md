# Step-by-Step Guide: Detecting Human Viruses in RNA-seq Data
## Using Kraken2 with a Custom Human Virus Database

---

## What is this guide for?

We have built a pipeline to detect human viruses (like VZV, CMV, HSV)
in RNA-seq data from human dorsal root ganglion (DRG) neurons.

**This guide will help you:**
1. Install the required tools
2. Build our custom virus database
3. Test the pipeline on one sample (SRR25745120) to verify it works
4. Run the pipeline on your own RNA-seq data
5. Send us the output files so we can analyse the results together

**You do NOT need to:**
- Make any plots
- Interpret the results
- Run all 13 of our samples
- Install any special hardware

**You just need to:**
- Follow the steps below
- Run on one test sample first
- Then run on your own samples
- Send us the output `.txt` files

---

## What you will need

- A Linux computer or HPC cluster
- At least 16 GB RAM
- At least 30 GB free disk space
- Internet connection
- Basic ability to type commands in a terminal

---

## OVERVIEW

```
STEP 1  →  Install tools (Conda + Kraken2)
STEP 2  →  Download the taxonomy files
STEP 3  →  Add our 17 virus sequences to database
STEP 4  →  Build the Kraken2 database
STEP 5  →  TEST: Run on our sample SRR25745120
STEP 6  →  Check your test result matches ours
STEP 7  →  Run on YOUR own samples
STEP 8  →  Send us the output files
```

---

## STEP 1 — Install Conda and Kraken2

### 1a. Install Miniconda

Conda is a tool that installs everything else automatically.

```bash
# Download the installer
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Run the installer
bash Miniconda3-latest-Linux-x86_64.sh

# When asked questions:
#   Press ENTER to read the license
#   Type 'yes' to accept the license
#   Press ENTER to confirm install location
#   Type 'yes' when asked to initialize conda

# Reload your terminal
source ~/.bashrc
```

### 1b. Check Conda installed correctly

```bash
conda --version
# Should show: conda 23.x.x  (any version is fine)
```

### 1c. Create a clean environment and install Kraken2

```bash
# Create environment
conda create -n kraken_viral python=3.10 -y

# Activate it (you must do this every time you open a new terminal)
conda activate kraken_viral

# Install Kraken2
conda install -c bioconda kraken2 -y
```

### 1d. Check Kraken2 installed correctly

```bash
kraken2 --version
# Should show: Kraken version 2.1.x
```

> **On an HPC cluster?** Kraken2 may already be installed.
> Try typing `kraken2 --version` first. If it works, skip Step 1c.
> If not, ask your system administrator or use the conda method above.

---

## STEP 2 — Create the database folder and download taxonomy

Kraken2 needs taxonomy files from NCBI to know how organisms are classified.

```bash
# Create a folder for your database
mkdir -p ~/human_virus_db

# Download taxonomy from NCBI
# (This takes 10-30 minutes depending on internet speed)
kraken2-build \
    --download-taxonomy \
    --use-ftp \
    --db ~/human_virus_db

echo "Taxonomy download complete!"
```

### Check it worked

```bash
ls ~/human_virus_db/taxonomy/

# You should see these files:
#   names.dmp
#   nodes.dmp
#   nucl_gb.accession2taxid  (this one is large, ~14 GB)
```

> **Slow internet or quota issues?**
> The `nucl_gb.accession2taxid` file is large (~14 GB uncompressed).
> If this fails, contact us and we can share the taxonomy files directly.

---

## STEP 3 — Add the 17 virus sequences to the database

We will provide you with **17 individual FASTA files** — one file per virus.
Each file already has the correct taxon ID embedded in the header
(in `kraken:taxid|TAXID` format) so Kraken2 assigns it correctly.

### Files we will send you

```
database/fasta/
├── NC_001348.1.fasta   ← VZV
├── NC_006273.2.fasta   ← CMV
├── NC_001806.2.fasta   ← HSV-1
├── NC_001798.2.fasta   ← HSV-2
├── NC_001664.4.fasta   ← HHV-6A
├── NC_009334.1.fasta   ← EBV
├── NC_001405.1.fasta   ← Adenovirus C
├── NC_001802.1.fasta   ← HIV-1
├── NC_002204.1.fasta   ← Influenza B
├── NC_007366.1.fasta   ← Flu A H3N2
├── NC_026431.1.fasta   ← Flu A H1N1
├── NC_045512.2.fasta   ← SARS-CoV-2
├── NC_002058.3.fasta   ← Poliovirus
├── NC_001498.1.fasta   ← Measles
├── NC_002200.1.fasta   ← Mumps
├── NC_001542.1.fasta   ← Rabies
└── NC_001612.1.fasta   ← Enterovirus A
```

### First check all 17 files are there

```bash
# Count how many FASTA files are in the folder
ls database/fasta/*.fasta | wc -l
# Should show: 17

# Check each file has a kraken:taxid header
grep "^>" database/fasta/*.fasta
# Every line should contain kraken:taxid|NUMBER
```

### Add each virus file to the database one by one

```bash
# Add all 17 files — run this block as-is
for fasta_file in database/fasta/*.fasta; do
    echo "Adding: $fasta_file"
    kraken2-build \
        --add-to-library $fasta_file \
        --db ~/human_virus_db \
        --no-masking
done

echo "All 17 viruses added!"
```

You should see 17 lines like:
```
Adding: database/fasta/NC_001348.1.fasta
Adding: database/fasta/NC_001405.1.fasta
... etc
```

> **Why individual files instead of one combined file?**
> Adding them one by one ensures each virus sequence is correctly
> linked to its taxon ID. This is the same method we used to build
> our validated database.

---

## STEP 4 — Build the Kraken2 database

This step creates the final searchable database.
It takes about 5-10 minutes.

```bash
kraken2-build \
    --build \
    --db ~/human_virus_db \
    --kmer-len 35 \
    --minimizer-len 31 \
    --threads 8

echo "Database build complete!"
```

### Check the database was built correctly

```bash
# Check these 3 files exist
ls -lh ~/human_virus_db/*.k2d

# Should show 3 files:
#   hash.k2d
#   opts.k2d
#   taxo.k2d
```

### Verify all 17 viruses are in the database

```bash
kraken2-inspect --db ~/human_virus_db | \
    grep -i "varicella\|simplexvirus\|cytomegalo\|roseolovirus\
\|lymphocrypto\|lentivirus\|adeno\|influenza\|corona\|measles\
\|mumps\|rabies\|entero"
```

You should see all 17 viruses listed. If you see them — your database
is ready to use!

---

## STEP 5 — TEST: Download and run one sample (SRR25745120)

Before running on your own data, please test the pipeline on our sample
**SRR25745120** so we can verify your results match ours.

### 5a. Download the test sample

```bash
# Create a folder for the test sample
mkdir -p ~/test_sample
cd ~/test_sample

# Download the two FASTQ files (paired-end, ~3 GB each)
wget -c https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR257/020/SRR25745120/SRR25745120_1.fastq.gz
wget -c https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR257/020/SRR25745120/SRR25745120_2.fastq.gz

# Check files downloaded correctly
ls -lh *.fastq.gz
# Should show two files, each about 2-4 GB
```

### 5b. Run Kraken2 on the test sample

```bash
# Create output folder
mkdir -p ~/test_results

# Run Kraken2
kraken2 \
    --db ~/human_virus_db \
    --paired \
    --gzip-compressed \
    --threads 8 \
    --report ~/test_results/SRR25745120_report.txt \
    --output ~/test_results/SRR25745120_output.txt \
    ~/test_sample/SRR25745120_1.fastq.gz \
    ~/test_sample/SRR25745120_2.fastq.gz

echo "Test run complete!"
```

This takes about 20-30 minutes.

---

## STEP 6 — Check your test result matches ours

After the run, check the key virus read counts:

```bash
echo "=== Checking virus reads in SRR25745120 ==="
echo ""
echo "VZV (should be ~99 reads):"
grep -w "10335" ~/test_results/SRR25745120_report.txt | awk '{print "  VZV reads: "$2}'

echo ""
echo "CMV (should be ~108 reads):"
grep -w "10359" ~/test_results/SRR25745120_report.txt | awk '{print "  CMV reads: "$2}'

echo ""
echo "HSV-1 (should be ~172 reads):"
grep -w "10298" ~/test_results/SRR25745120_report.txt | awk '{print "  HSV-1 reads: "$2}'

echo ""
echo "HHV-6A (should be ~390 reads):"
grep -w "32603" ~/test_results/SRR25745120_report.txt | awk '{print "  HHV-6A reads: "$2}'
```

### Expected results for SRR25745120

| Virus | Taxon ID | Expected reads |
|-------|----------|----------------|
| VZV | 10335 | ~99 reads |
| CMV | 10359 | ~108 reads |
| HSV-1 | 10298 | ~172 reads |
| HSV-2 | 10310 | ~4 reads |
| HHV-6A | 32603 | ~390 reads |
| EBV | 12509 | 0 reads |
| Adenovirus C | 129951 | ~27 reads |

If your numbers are close to these — the pipeline is working correctly!
Small differences (±10%) are normal.

> **Results look very different?**
> Please send us your report file and we will help troubleshoot.

---

## STEP 7 — Run on YOUR own samples

Once the test passes, run the pipeline on your own RNA-seq data.

### For paired-end samples (two FASTQ files: _1 and _2)

```bash
# Replace YOUR_SAMPLE with your actual sample name
# Replace /path/to/ with the actual location of your files

kraken2 \
    --db ~/human_virus_db \
    --paired \
    --gzip-compressed \
    --threads 8 \
    --report ~/test_results/YOUR_SAMPLE_report.txt \
    --output ~/test_results/YOUR_SAMPLE_output.txt \
    /path/to/YOUR_SAMPLE_1.fastq.gz \
    /path/to/YOUR_SAMPLE_2.fastq.gz
```

### For single-end samples (one FASTQ file only)

```bash
kraken2 \
    --db ~/human_virus_db \
    --gzip-compressed \
    --threads 8 \
    --report ~/test_results/YOUR_SAMPLE_report.txt \
    --output ~/test_results/YOUR_SAMPLE_output.txt \
    /path/to/YOUR_SAMPLE.fastq.gz
```

### Running multiple samples

```bash
# Save this as run_my_samples.sh
# Edit the sample names and paths to match your files

#!/bin/bash
DB=~/human_virus_db
OUT=~/test_results
mkdir -p $OUT

# List your sample names here
SAMPLES=(
    "SAMPLE1"
    "SAMPLE2"
    "SAMPLE3"
)

for SAMPLE in "${SAMPLES[@]}"; do
    echo "Processing $SAMPLE ..."
    kraken2 --db $DB --paired --gzip-compressed --threads 8 \
        --report $OUT/${SAMPLE}_report.txt \
        --output $OUT/${SAMPLE}_output.txt \
        /path/to/${SAMPLE}_1.fastq.gz \
        /path/to/${SAMPLE}_2.fastq.gz
    echo "Done: $SAMPLE"
done

echo "ALL DONE"
```

Run it with:
```bash
bash run_my_samples.sh
```

---

## STEP 8 — Send us the output files

When all your samples are done, please send us:

### Which files to send

**For EACH sample, send us TWO files:**

```
SAMPLENAME_report.txt    ← small file (~5 KB) — REQUIRED
SAMPLENAME_output.txt    ← large file (~1 GB) — optional but useful
```

> The `_report.txt` file is the most important one.
> It is small (a few KB) and contains the summary of all classified reads.
> The `_output.txt` file has read-by-read details — only send this
> if we ask for it, as it can be very large.

### Where the files are

```bash
# List all your result files
ls -lh ~/test_results/

# Check file sizes
du -sh ~/test_results/*_report.txt
```

### How to send

You can send the `_report.txt` files by:
- Email attachment (they are very small, just a few KB each)
- File sharing service (Google Drive, Dropbox, WeTransfer)
- Direct transfer to our server (we can provide sftp details)

### What to include when you send

Please also tell us:
1. The organism/tissue your RNA-seq samples are from
2. Whether samples are paired-end or single-end
3. Any other relevant information about the samples

---

## TROUBLESHOOTING

### "command not found: kraken2"
```bash
# You need to activate the conda environment first
conda activate kraken_viral

# Or add to PATH if compiled manually
export PATH=~/kraken2_bin:$PATH
```

### "database does not contain necessary file taxo.k2d"
```bash
# The database build failed. Start again:
rm -rf ~/human_virus_db
mkdir -p ~/human_virus_db
# Then redo Steps 2, 3, 4
```

### "No such file or directory" for FASTQ files
```bash
# Check your file exists and the path is correct
ls /path/to/your/file.fastq.gz

# Check your current directory
pwd
ls *.fastq.gz
```

### Download failed or very slow
```bash
# Use -c flag to resume an interrupted download
wget -c https://ftp.sra.ebi.ac.uk/.../SRR25745120_1.fastq.gz

# Or use prefetch from SRA toolkit
prefetch SRR25745120
fasterq-dump SRR25745120
gzip SRR25745120_*.fastq
```

### Out of memory error
```bash
# Reduce number of threads
# Change --threads 8 to --threads 2
# Or request more memory from your HPC scheduler
```

### Not sure if your results are correct?
Send us your `_report.txt` file and we will check it for you.

---

## QUICK REFERENCE

### All virus taxon IDs we look for

| Taxon ID | Virus | What it causes |
|----------|-------|----------------|
| 10335 | VZV | Chickenpox / Shingles |
| 10359 | CMV | Cytomegalovirus infection |
| 10298 | HSV-1 | Cold sores |
| 10310 | HSV-2 | Genital herpes |
| 32603 | HHV-6A | Roseola |
| 12509 | EBV | Mononucleosis (mono) |
| 129951 | Adenovirus C | Common cold |
| 11676 | HIV-1 | AIDS |
| 518987 | Influenza B | Flu |
| 335341 | Flu A H3N2 | Flu |
| 641809 | Flu A H1N1 | Swine flu |
| 2697049 | SARS-CoV-2 | COVID-19 |
| 138950 | Poliovirus | Polio |
| 11234 | Measles | Measles |
| 2560602 | Mumps | Mumps |
| 11292 | Rabies | Rabies |
| 138948 | Enterovirus A | Hand foot mouth disease |

### All commands in one place

```bash
# Step 1: Setup
conda create -n kraken_viral python=3.10 -y
conda activate kraken_viral
conda install -c bioconda kraken2 -y

# Step 2: Taxonomy
mkdir -p ~/human_virus_db
kraken2-build --download-taxonomy --use-ftp --db ~/human_virus_db

# Step 3: Add all 17 virus files one by one
for fasta_file in database/fasta/*.fasta; do
    kraken2-build \
        --add-to-library $fasta_file \
        --db ~/human_virus_db --no-masking
done

# Step 4: Build
kraken2-build --build --db ~/human_virus_db \
    --kmer-len 35 --minimizer-len 31 --threads 8

# Step 5: Test run
mkdir -p ~/test_sample ~/test_results
cd ~/test_sample
wget -c https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR257/020/SRR25745120/SRR25745120_1.fastq.gz
wget -c https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR257/020/SRR25745120/SRR25745120_2.fastq.gz

kraken2 --db ~/human_virus_db \
    --paired --gzip-compressed --threads 8 \
    --report ~/test_results/SRR25745120_report.txt \
    --output ~/test_results/SRR25745120_output.txt \
    ~/test_sample/SRR25745120_1.fastq.gz \
    ~/test_sample/SRR25745120_2.fastq.gz

# Step 6: Verify
grep -w "10335" ~/test_results/SRR25745120_report.txt
# Should show ~99 VZV reads

# Step 7: Run your samples
kraken2 --db ~/human_virus_db \
    --paired --gzip-compressed --threads 8 \
    --report ~/test_results/YOUR_SAMPLE_report.txt \
    --output ~/test_results/YOUR_SAMPLE_output.txt \
    YOUR_SAMPLE_1.fastq.gz YOUR_SAMPLE_2.fastq.gz

# Step 8: Send us the _report.txt files!
ls ~/test_results/*_report.txt
```

---

*Pipeline developed at Helmholtz Institute for Infection Research (HZI).
For questions or help, please contact the repository owner.
Kraken2 v2.1.3 | August 2026*
