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

---

## What you will need

- A Linux computer or HPC cluster
- At least 16 GB RAM
- At least 30 GB free disk space

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
---

## STEP 3 — Download and add the 17 virus sequences to the database

All 17 virus reference FASTA files are already in this GitHub repository
in the `database/fasta/` folder. You just need to clone the repository
and add them to the database.

### 3a. Clone this repository

```bash
# Clone the repository to your computer/server
git clone https://github.com/painhelmholtz-ops/Custom-kraken2.git

# Go into the repository folder
cd Custom-kraken2

# Check all 17 FASTA files are there
ls database/fasta/*.fasta | wc -l
# Should show: 17
```

### 3b. Check the files look correct

```bash
# See all virus names and their taxon IDs
grep "^>" database/fasta/*.fasta

# You should see 17 lines like this:
# database/fasta/NC_001348.1.fasta:>NC_001348.1|kraken:taxid|10335 VZV_Human_alphaherpesvirus_3
# database/fasta/NC_001405.1.fasta:>NC_001405.1|kraken:taxid|129951 Human_mastadenovirus_C
# ... and 15 more
```

### 3c. Add all 17 files to the database

```bash
# Make sure you are inside the Custom-kraken2 folder
cd Custom-kraken2

# Add all 17 virus files to the database — run this block as-is
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
Adding: database/fasta/NC_001498.1.fasta
... etc
Adding: database/fasta/NC_045512.2.fasta
All 17 viruses added!
```

> **Why individual files instead of one combined file?**
> Adding them one by one ensures each virus sequence is correctly
> linked to its taxon ID (`kraken:taxid` in the header).
> This is exactly the same method we used to build our validated database.

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

This will take few minutes.

---

## STEP 6 — Check your test result matches ours

After the run, compare your results with our reference result file
which is already in this repository at:
```
results/SRR25745120/SRR25745120_report.txt
```

### 6a. Quick check — key virus read counts

```bash
echo "=== YOUR results for SRR25745120 ==="
echo ""
echo "VZV (taxid 10335) — expected ~99 reads:"
grep -w "10335" ~/test_results/SRR25745120_report.txt | awk '{print "  Your result: "$2" reads"}'

echo ""
echo "CMV (taxid 10359) — expected ~108 reads:"
grep -w "10359" ~/test_results/SRR25745120_report.txt | awk '{print "  Your result: "$2" reads"}'

echo ""
echo "HSV-1 (taxid 10298) — expected ~172 reads:"
grep -w "10298" ~/test_results/SRR25745120_report.txt | awk '{print "  Your result: "$2" reads"}'

echo ""
echo "HHV-6A (taxid 32603) — expected ~390 reads:"
grep -w "32603" ~/test_results/SRR25745120_report.txt | awk '{print "  Your result: "$2" reads"}'
```

### 6b. Compare with our reference report file

```bash
# Our reference report is in the repository
# Compare your result with ours line by line

echo "=== OUR reference results (from repository) ==="
grep -w "10335\|10359\|10298\|10310\|32603\|12509\|129951\|11676\|2697049" \
    results/SRR25745120/SRR25745120_report.txt | \
    awk '{printf "  %-40s reads: %s\n", $NF, $2}'

echo ""
echo "=== YOUR results ==="
grep -w "10335\|10359\|10298\|10310\|32603\|12509\|129951\|11676\|2697049" \
    ~/test_results/SRR25745120_report.txt | \
    awk '{printf "  %-40s reads: %s\n", $NF, $2}'
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
| HIV-1 | 11676 | 0 reads |
| SARS-CoV-2 | 2697049 | ~4,432 reads* |

> *SARS-CoV-2 reads are false positives from human genome k-mer overlap.
> This is expected and does not affect herpesvirus results.

If your numbers are close to these — the pipeline is working correctly.

> **Results look very different?**
> Please send us your `_report.txt` file and we will help troubleshoot.

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

### Which files to send

**For EACH sample, send us TWO files:**

```
SAMPLENAME_report.txt    ← small file (~5 KB) — REQUIRED
SAMPLENAME_output.txt    ← large file (~1 GB) — Machine readable 
```

> The `_report.txt` file is the most important one.
> It is small (a few KB) and contains the summary of all classified reads.

### Where the files are

```bash
# List all your result files
ls -lh ~/test_results/

# Check file sizes
du -sh ~/test_results/*_report.txt
```

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

# Step 2: Clone repository (gets all 17 FASTA files automatically)
git clone https://github.com/painhelmholtz-ops/Custom-kraken2.git
cd Custom-kraken2

# Step 3: Download taxonomy
mkdir -p ~/human_virus_db
kraken2-build --download-taxonomy --use-ftp --db ~/human_virus_db

# Step 4: Add all 17 virus files (already in database/fasta/ folder)
for fasta_file in database/fasta/*.fasta; do
    echo "Adding: $fasta_file"
    kraken2-build \
        --add-to-library $fasta_file \
        --db ~/human_virus_db --no-masking
done

# Step 5: Build database
kraken2-build --build --db ~/human_virus_db \
    --kmer-len 35 --minimizer-len 31 --threads 8

# Step 6: Download test sample
mkdir -p ~/test_sample ~/test_results
wget -c -P ~/test_sample \
    https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR257/020/SRR25745120/SRR25745120_1.fastq.gz
wget -c -P ~/test_sample \
    https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR257/020/SRR25745120/SRR25745120_2.fastq.gz

# Step 7: Run test sample
kraken2 --db ~/human_virus_db \
    --paired --gzip-compressed --threads 8 \
    --report ~/test_results/SRR25745120_report.txt \
    --output ~/test_results/SRR25745120_output.txt \
    ~/test_sample/SRR25745120_1.fastq.gz \
    ~/test_sample/SRR25745120_2.fastq.gz

# Step 8: Compare your result with our reference
echo "=== YOUR result ==="
grep -w "10335\|10359\|10298\|32603" \
    ~/test_results/SRR25745120_report.txt | \
    awk '{print $NF": "$2" reads"}'

echo ""
echo "=== OUR reference result (from repository) ==="
grep -w "10335\|10359\|10298\|32603" \
    results/SRR25745120/SRR25745120_report.txt | \
    awk '{print $NF": "$2" reads"}'

# Step 9: Run your own samples
kraken2 --db ~/human_virus_db \
    --paired --gzip-compressed --threads 8 \
    --report ~/test_results/YOUR_SAMPLE_report.txt \
    --output ~/test_results/YOUR_SAMPLE_output.txt \
    YOUR_SAMPLE_1.fastq.gz YOUR_SAMPLE_2.fastq.gz

# Step 10: Send us the _report.txt files!
ls ~/test_results/*_report.txt
```

---

*Pipeline developed at Helmholtz Institute for Infection Research (HZI).
For questions or help, please contact the repository owner.
Kraken2 v2.1.3 | August 2026*
