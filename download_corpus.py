#!/usr/bin/env python3
"""
download_corpus.py
===================
Downloads the official Bharatiya Nyaya Sanhita (BNS), Bharatiya Nagarik Suraksha Sanhita (BNSS),
and Bharatiya Sakshya Adhiniyam (BSA) PDFs directly from the Ministry of Home Affairs.

It skips downloading if the files already exist in the Raw_Data/ folder.
"""

import os
import urllib.request
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Hardcoded MHA direct URLs for the 3 acts
CORPUS_FILES = {
    "bns.pdf": "https://www.mha.gov.in/sites/default/files/250883_english_01042024.pdf",
    "bnss.pdf": "https://www.mha.gov.in/sites/default/files/2024-04/250884_2_english_01042024.pdf",
    # MHA sometimes changes the BSA link, but this is the static copy hosted for the new laws
    "bsa.pdf": "https://www.mha.gov.in/sites/default/files/250882_english_01042024.pdf" 
}

def download_corpus():
    raw_dir = Path("Raw_Data")
    raw_dir.mkdir(exist_ok=True)
    
    print("\n--- Nyaya Mitra: Corpus Verification ---")
    
    all_downloaded = True
    for filename, url in CORPUS_FILES.items():
        filepath = raw_dir / filename
        if filepath.exists():
            print(f"[OK] {filename} already exists. Skipping download.")
        else:
            print(f"[FETCH] Downloading {filename} from {url}...")
            try:
                # Use a standard user-agent so MHA's firewall doesn't block the request
                req = urllib.request.Request(
                    url, 
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )
                with urllib.request.urlopen(req) as response, open(filepath, 'wb') as out_file:
                    out_file.write(response.read())
                print(f"[SUCCESS] Saved to {filepath}")
            except Exception as e:
                print(f"[ERROR] Failed to download {filename}: {e}")
                all_downloaded = False
                
    if all_downloaded:
        print("--- All corpus files are ready. ---\n")
    else:
        print("--- Some files failed to download. You may need to download them manually. ---\n")

if __name__ == "__main__":
    download_corpus()
