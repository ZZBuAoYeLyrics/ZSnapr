#!/usr/bin/env python3
import os
import shutil
import sys
from pathlib import Path

def clean_pycache(root_dir="."):
    """
    Clean all __pycache__ directories and .pyc files recursively
    
    Args:
        root_dir (str): Root directory to start cleaning from
    """
    root_path = Path(root_dir).resolve()
    
    if not root_path.exists():
        print(f"Error: Directory '{root_dir}' does not exist!")
        return False
    
    print(f"Cleaning Python cache files in: {root_path}")
    print("-" * 50)
    
    # Counters for statistics
    pycache_dirs_removed = 0
    pyc_files_removed = 0
    pyo_files_removed = 0
    
    # Find and remove __pycache__ directories
    for pycache_dir in root_path.rglob("__pycache__"):
        if pycache_dir.is_dir():
            try:
                # Count files before removal
                file_count = len(list(pycache_dir.rglob("*")))
                shutil.rmtree(pycache_dir)
                pycache_dirs_removed += 1
                print(f"✓ Removed __pycache__ directory: {pycache_dir.relative_to(root_path)} ({file_count} files)")
            except Exception as e:
                print(f"✗ Failed to remove {pycache_dir}: {e}")
    
    # Find and remove .pyc files
    for pyc_file in root_path.rglob("*.pyc"):
        try:
            pyc_file.unlink()
            pyc_files_removed += 1
            print(f"✓ Removed .pyc file: {pyc_file.relative_to(root_path)}")
        except Exception as e:
            print(f"✗ Failed to remove {pyc_file}: {e}")
    
    # Find and remove .pyo files
    for pyo_file in root_path.rglob("*.pyo"):
        try:
            pyo_file.unlink()
            pyo_files_removed += 1
            print(f"✓ Removed .pyo file: {pyo_file.relative_to(root_path)}")
        except Exception as e:
            print(f"✗ Failed to remove {pyo_file}: {e}")
    
    # Print summary
    print("-" * 50)
    print("Cleanup Summary:")
    print(f"  __pycache__ directories removed: {pycache_dirs_removed}")
    print(f"  .pyc files removed: {pyc_files_removed}")
    print(f"  .pyo files removed: {pyo_files_removed}")
    
    total_items = pycache_dirs_removed + pyc_files_removed + pyo_files_removed
    if total_items > 0:
        print(f"✓ Successfully cleaned {total_items} items!")
    else:
        print("✓ No cache files found - project is already clean!")
    
    return True

def main():
    """Main function to handle command line arguments"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Clean Python cache files (__pycache__, .pyc, .pyo)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python clean_cache.py                    # Clean current directory
  python clean_cache.py /path/to/project   # Clean specific directory
  python clean_cache.py --dry-run          # Show what would be cleaned
        """
    )
    
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to clean (default: current directory)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be cleaned without actually removing files"
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("DRY RUN MODE - No files will be actually removed")
        print("=" * 50)
        dry_run_scan(args.directory)
    else:
        clean_pycache(args.directory)

def dry_run_scan(root_dir="."):
    """Scan and show what would be cleaned without removing anything"""
    root_path = Path(root_dir).resolve()
    
    if not root_path.exists():
        print(f"Error: Directory '{root_dir}' does not exist!")
        return
    
    print(f"Scanning for Python cache files in: {root_path}")
    print("-" * 50)
    
    pycache_dirs = list(root_path.rglob("__pycache__"))
    pyc_files = list(root_path.rglob("*.pyc"))
    pyo_files = list(root_path.rglob("*.pyo"))
    
    if pycache_dirs:
        print("__pycache__ directories found:")
        for pycache_dir in pycache_dirs:
            file_count = len(list(pycache_dir.rglob("*")))
            print(f"  - {pycache_dir.relative_to(root_path)} ({file_count} files)")
    
    if pyc_files:
        print("\n.pyc files found:")
        for pyc_file in pyc_files:
            print(f"  - {pyc_file.relative_to(root_path)}")
    
    if pyo_files:
        print("\n.pyo files found:")
        for pyo_file in pyo_files:
            print(f"  - {pyo_file.relative_to(root_path)}")
    
    total_items = len(pycache_dirs) + len(pyc_files) + len(pyo_files)
    print("-" * 50)
    print(f"Total items that would be cleaned: {total_items}")
    
    if total_items > 0:
        print("\nRun without --dry-run to actually clean these files.")
    else:
        print("No cache files found - project is already clean!")

if __name__ == "__main__":
    main()