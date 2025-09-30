#!/usr/bin/env python3
"""
Find Latest Versions

Script to scan quality_evaluation_output and find the latest version
of every leaf node (files with timestamps).
"""

import os
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def extract_timestamp(filename):
    """Extract timestamp from filename in format YYYYMMDD_HHMMSS"""
    # Look for pattern: _YYYYMMDD_HHMMSS
    match = re.search(r'_(\d{8})_(\d{6})', filename)
    if match:
        date_str = match.group(1)  # YYYYMMDD
        time_str = match.group(2)  # HHMMSS

        try:
            # Parse to datetime for comparison
            dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
            return dt, f"{date_str}_{time_str}"
        except ValueError:
            return None, None

    return None, None

def get_base_name(filename):
    """Get base name without timestamp and extension"""
    # Remove .md extension
    name = filename.replace('.md', '')

    # Remove timestamp pattern
    base = re.sub(r'_\d{8}_\d{6}$', '', name)

    return base

def find_latest_versions(output_dir, quiet=False):
    """Find latest version of every leaf node file"""

    if not quiet:
        print(f"🔍 Scanning directory: {output_dir}")
        print()

    # Track files by their base name and directory
    # Key: (directory, base_name), Value: list of (full_path, timestamp_dt, timestamp_str)
    file_groups = defaultdict(list)

    # Scan all markdown files
    for root, dirs, files in os.walk(output_dir):
        for filename in files:
            if not filename.endswith('.md'):
                continue

            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(root, output_dir)

            # Extract timestamp
            timestamp_dt, timestamp_str = extract_timestamp(filename)

            # Get base name
            base_name = get_base_name(filename)

            # Group by directory and base name
            key = (rel_path, base_name)
            file_groups[key].append((full_path, timestamp_dt, timestamp_str, filename))

    # Find latest version for each group
    latest_versions = {}

    for (directory, base_name), files in file_groups.items():
        if len(files) == 1:
            # Only one version
            full_path, timestamp_dt, timestamp_str, filename = files[0]
            latest_versions[(directory, base_name)] = {
                'path': full_path,
                'filename': filename,
                'timestamp': timestamp_str,
                'versions': 1
            }
        else:
            # Multiple versions - find latest
            files_with_timestamps = [(f, dt, ts, fn) for f, dt, ts, fn in files if dt is not None]

            if files_with_timestamps:
                # Sort by timestamp (most recent first)
                files_with_timestamps.sort(key=lambda x: x[1], reverse=True)
                latest_path, latest_dt, latest_ts, latest_fn = files_with_timestamps[0]

                latest_versions[(directory, base_name)] = {
                    'path': latest_path,
                    'filename': latest_fn,
                    'timestamp': latest_ts,
                    'versions': len(files_with_timestamps)
                }

    # Display results grouped by directory
    if not quiet:
        print("📊 Latest versions by directory:\n")

        # Group by directory for display
        by_directory = defaultdict(list)
        for (directory, base_name), info in latest_versions.items():
            by_directory[directory].append((base_name, info))

        # Sort directories
        for directory in sorted(by_directory.keys()):
            print(f"📁 {directory}")

            # Sort files within directory
            files = sorted(by_directory[directory], key=lambda x: x[0])

            for base_name, info in files:
                versions_text = f"({info['versions']} version{'s' if info['versions'] > 1 else ''})" if info['versions'] > 1 else ""
                timestamp_text = f"[{info['timestamp']}]" if info['timestamp'] else ""

                rel_file_path = os.path.relpath(info['path'], output_dir)
                print(f"   ✓ {base_name} {timestamp_text} {versions_text}")
                print(f"     → {rel_file_path}")

            print()

        # Summary
        total_files = len(latest_versions)
        multiple_versions = sum(1 for info in latest_versions.values() if info['versions'] > 1)

        print(f"📈 Summary:")
        print(f"   Total leaf nodes: {total_files}")
        print(f"   Files with multiple versions: {multiple_versions}")
        print(f"   Files with single version: {total_files - multiple_versions}")

    return latest_versions

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Find latest versions of files')
    parser.add_argument('--output-paths', action='store_true', help='Output only file paths (one per line)')
    args = parser.parse_args()

    output_dir = "../../quality_evaluation_output"

    if not os.path.exists(output_dir):
        print(f"❌ Directory not found: {output_dir}")
        exit(1)

    # Use quiet mode when outputting paths only
    latest_versions = find_latest_versions(output_dir, quiet=args.output_paths)

    # If --output-paths flag is set, output only paths
    if args.output_paths:
        for (directory, base_name), info in sorted(latest_versions.items(), key=lambda x: x[1]['path']):
            rel_path = os.path.relpath(info['path'], output_dir)
            print(rel_path)