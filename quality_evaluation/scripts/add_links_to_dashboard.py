#!/usr/bin/env python3
"""
Add Links to Dashboard

Script to scan Confluence for comparison pages and add links to the dashboard.
"""

import os
import sys
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scan_confluence_links import scan_confluence_pages

def update_dashboard_with_links():
    """Update the dashboard markdown file with Confluence links"""

    # Get the links from Confluence
    print("📋 Scanning Confluence for comparison analysis pages...")
    comparison_links = scan_confluence_pages()

    if not comparison_links:
        print("❌ Failed to get comparison links")
        return

    print(f"\n📝 Updating dashboard with links...")

    # Read the current dashboard
    dashboard_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        '..',
        'quality_evaluation_output',
        'travel_usability_dashboard.md'
    )

    with open(dashboard_path, 'r') as f:
        content = f.read()

    # Split into lines
    lines = content.split('\n')

    # Find the table and update ratings with links
    updated_lines = []

    for line in lines:
        # Check if this is a data row (starts with |)
        if line.startswith('|') and not line.startswith('|---') and 'Destination' not in line:
            # Extract city name (first column)
            parts = [p.strip() for p in line.split('|')]
            if len(parts) < 7:  # Need at least 7 parts (empty, city, 5 features, empty)
                updated_lines.append(line)
                continue

            city = parts[1]

            # Feature columns mapping (index -> feature name)
            feature_indices = {
                2: 'autocomplete',
                3: 'relevance',
                4: 'five_partners',
                5: 'hero_pos',
                6: 'distance'
            }

            # Update each rating cell with link if available
            for idx, feature in feature_indices.items():
                if city in comparison_links and feature in comparison_links[city]:
                    # Get the link
                    link = comparison_links[city][feature]

                    # Get current rating (strip any existing markdown links)
                    rating = parts[idx]

                    # Remove any existing markdown link syntax
                    # Extract just the rating text if already has a link
                    rating_match = re.match(r'\[([^\]]+)\]\([^)]+\)', rating)
                    if rating_match:
                        rating = rating_match.group(1)

                    # Skip if no rating or is dash
                    if rating and rating != '-/-/-/-':
                        # Wrap rating in link (single brackets only)
                        parts[idx] = f"[{rating}]({link})"

            # Reconstruct line
            updated_line = '| ' + ' | '.join(parts[1:-1]) + ' |'
            updated_lines.append(updated_line)
        else:
            updated_lines.append(line)

    # Write updated content
    updated_content = '\n'.join(updated_lines)

    with open(dashboard_path, 'w') as f:
        f.write(updated_content)

    print(f"✅ Dashboard updated with links!")
    print(f"📄 File: {dashboard_path}")

if __name__ == "__main__":
    update_dashboard_with_links()