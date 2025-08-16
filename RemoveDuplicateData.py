import os
import csv
import hashlib
from collections import defaultdict

def get_file_hash(filepath):
    """Calculate MD5 hash of file content"""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

def get_csv_content_hash(filepath):
    """Calculate hash of CSV content (ignoring potential formatting differences)"""
    try:
        content = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                # Normalize by stripping whitespace from each cell
                normalized_row = [cell.strip() for cell in row]
                content.append(tuple(normalized_row))
        
        # Convert to string and hash
        content_str = str(sorted(content))
        return hashlib.md5(content_str.encode()).hexdigest()
    except Exception as e:
        print(f"Error processing CSV {filepath}: {e}")
        return None

def find_and_remove_duplicates(folder_path):
    """Find duplicate CSV files and remove them, keeping the first one"""
    if not os.path.exists(folder_path):
        print(f"Folder {folder_path} does not exist!")
        return
    
    # Get all CSV files
    csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    
    if not csv_files:
        print("No CSV files found in the folder.")
        return
    
    print(f"Found {len(csv_files)} CSV files. Checking for duplicates...")
    
    # Group files by their content hash
    hash_to_files = defaultdict(list)
    
    for filename in csv_files:
        filepath = os.path.join(folder_path, filename)
        file_hash = get_csv_content_hash(filepath)
        
        if file_hash:
            hash_to_files[file_hash].append((filename, filepath))
    
    # Find and handle duplicates
    total_duplicates = 0
    for file_hash, files in hash_to_files.items():
        if len(files) > 1:
            print(f"\nFound {len(files)} duplicate files:")
            
            # Sort by filename to keep the earliest date
            files.sort(key=lambda x: x[0])
            
            # Keep the first file, delete the rest
            keep_file = files[0]
            duplicate_files = files[1:]
            
            print(f"  KEEPING: {keep_file[0]}")
            
            for dup_filename, dup_filepath in duplicate_files:
                print(f"  DELETING: {dup_filename}")
                try:
                    os.remove(dup_filepath)
                    total_duplicates += 1
                except Exception as e:
                    print(f"    Error deleting {dup_filename}: {e}")
    
    print(f"\nSummary:")
    print(f"  Total files processed: {len(csv_files)}")
    print(f"  Duplicate files deleted: {total_duplicates}")
    print(f"  Remaining files: {len(csv_files) - total_duplicates}")

def main():
    folder_path = 'sharesansarTSP'  # Same folder as your scraper
    
    print("=== CSV Duplicate Remover ===")
    print(f"Scanning folder: {folder_path}")
    
    # Ask for confirmation
    response = input(f"\nThis will delete duplicate CSV files in '{folder_path}'. Continue? (y/N): ")
    if response.lower() != 'y':
        print("Operation cancelled.")
        return
    
    find_and_remove_duplicates(folder_path)

if __name__ == '__main__':
    main()