#!/usr/bin/env python3
"""
Extract Dashboard Data

Script to extract ratings from all comparison analysis files and structure them for the dashboard.
"""

import os
import re
from pathlib import Path
from collections import defaultdict

def extract_overall_ratings(file_path):
    """Extract overall ratings from a comparison markdown file"""

    with open(file_path, 'r') as f:
        content = f.read()

    # Find the table with Overall rating row
    # Look for the last row in the feature table
    table_match = re.search(r'\| Overall rating \|(.+)', content)

    if not table_match:
        return None

    # Extract ratings for each website
    ratings_text = table_match.group(1)

    # Split by | and extract numeric ratings from each cell
    # Remove trailing | first
    ratings_text = ratings_text.rstrip('|').strip()
    cells = [cell.strip() for cell in ratings_text.split('|')]

    ratings = {}
    website_order = ['Skyscanner', 'Google Travel', 'Booking.com', 'Agoda']

    for idx, cell in enumerate(cells):
        if idx >= len(website_order):
            break
        # Extract rating like "7/7" or "6/7"
        rating_match = re.search(r'(\d+)/7', cell)
        if rating_match:
            ratings[website_order[idx]] = rating_match.group(1)

    return ratings

def scan_comparison_files():
    """Scan all comparison analysis files and extract data"""

    base_path = Path('/Users/yongqiwu/code/quality-check/quality_evaluation_output/comparison_analysis')

    # Structure: {feature: {city: {website: rating}}}
    data = defaultdict(lambda: defaultdict(dict))

    # Feature name mapping (directory name -> display name)
    feature_display = {
        'autocomplete_for_destinations_hotels': 'Autocomplete for destinations hotels',
        'relevance_of_top_listings': 'Relevance of top listings',
        'five_partners_per_hotel': 'Five partners per hotel',
        'hero_position_partner_mix': 'Hero position partner mix',
        'distance_accuracy': 'Distance accuracy'
    }

    # Find all markdown files
    for feature_dir in base_path.iterdir():
        if not feature_dir.is_dir():
            continue

        feature_name = feature_dir.name
        feature_display_name = feature_display.get(feature_name, feature_name)

        for city_dir in feature_dir.iterdir():
            if not city_dir.is_dir():
                continue

            city_name = city_dir.name

            # Look for markdown files (use latest timestamp)
            md_files = list(city_dir.rglob('*.md'))

            if not md_files:
                continue

            # Get the latest file
            latest_file = sorted(md_files)[-1]

            # Extract ratings
            ratings = extract_overall_ratings(latest_file)

            if ratings:
                data[feature_display_name][city_name] = ratings
                print(f"Extracted: {feature_display_name} / {city_name} -> {ratings}")

    return data

def build_dashboard_table(data):
    """Build the markdown table for the dashboard"""

    # Get all cities and features
    all_cities = set()
    all_features = set()

    for feature, cities in data.items():
        all_features.add(feature)
        all_cities.update(cities.keys())

    # Sort for consistency
    sorted_cities = sorted(all_cities)
    sorted_features = [
        'Autocomplete for destinations hotels',
        'Relevance of top listings',
        'Five partners per hotel',
        'Hero position partner mix',
        'Distance accuracy'
    ]

    # Filter features that actually have data
    sorted_features = [f for f in sorted_features if f in all_features]

    # Build table header
    header = "| Destination | " + " | ".join(sorted_features) + " |"
    separator = "|" + "|".join(["-------------"] * (len(sorted_features) + 1)) + "|"

    lines = [header, separator]

    # Build data rows
    for city in sorted_cities:
        row_parts = [city]

        for feature in sorted_features:
            if city in data[feature]:
                ratings = data[feature][city]
                # Format: Skyscanner/Google Travel/Booking.com/Agoda
                rating_str = "/".join([
                    ratings.get('Skyscanner', '-'),
                    ratings.get('Google Travel', '-'),
                    ratings.get('Booking.com', '-'),
                    ratings.get('Agoda', '-')
                ])
            else:
                rating_str = "-/-/-/-"

            row_parts.append(rating_str)

        row = "| " + " | ".join(row_parts) + " |"
        lines.append(row)

    return "\n".join(lines), sorted_cities, sorted_features, data

def calculate_statistics(data, cities, features):
    """Calculate summary statistics"""

    website_totals = defaultdict(lambda: {'sum': 0, 'count': 0})

    for feature in features:
        for city in cities:
            if city in data[feature]:
                ratings = data[feature][city]
                for website, rating in ratings.items():
                    if rating != '-':
                        website_totals[website]['sum'] += int(rating)
                        website_totals[website]['count'] += 1

    # Calculate averages
    website_averages = {}
    for website, totals in website_totals.items():
        if totals['count'] > 0:
            avg = totals['sum'] / totals['count']
            website_averages[website] = {
                'average': avg,
                'count': totals['count']
            }

    return website_averages

def generate_dashboard(data, table, cities, features, stats):
    """Generate the complete dashboard markdown"""

    dashboard = []
    dashboard.append("# Travel Usability Dashboard")
    dashboard.append("")
    dashboard.append("*Format: Skyscanner/Google Travel/Booking.com/Agoda*")
    dashboard.append("")
    dashboard.append(table)
    dashboard.append("")
    dashboard.append("## Summary Ratings by Website")
    dashboard.append("")
    dashboard.append("| Website | Average Overall Rating | Data Points |")
    dashboard.append("|---------|----------------------|-------------|")

    # Sort by average rating
    sorted_websites = sorted(stats.items(), key=lambda x: x[1]['average'], reverse=True)

    for website, data_stats in sorted_websites:
        avg = data_stats['average']
        count = data_stats['count']
        dashboard.append(f"| **{website}** | {avg:.1f}/7 | {count} evaluations |")

    dashboard.append("")
    dashboard.append("## Key Insights")
    dashboard.append("")

    # Feature-level insights
    dashboard.append("### Best Performers by Feature")
    dashboard.append("")

    for idx, feature in enumerate(features, 1):
        feature_data = data[feature]

        # Calculate average by website for this feature
        website_feature_avg = defaultdict(lambda: {'sum': 0, 'count': 0})

        for city, ratings in feature_data.items():
            for website, rating in ratings.items():
                if rating != '-':
                    website_feature_avg[website]['sum'] += int(rating)
                    website_feature_avg[website]['count'] += 1

        # Get averages
        feature_averages = []
        for website, totals in website_feature_avg.items():
            if totals['count'] > 0:
                avg = totals['sum'] / totals['count']
                feature_averages.append((website, avg, totals['count']))

        if feature_averages:
            feature_averages.sort(key=lambda x: x[1], reverse=True)
            winner = feature_averages[0]

            dashboard.append(f"{idx}. **{feature}**")
            dashboard.append(f"   - Winner: **{winner[0]} ({winner[1]:.1f} avg)**")
            if len(feature_averages) > 1:
                runner_up = feature_averages[1]
                dashboard.append(f"   - Runner-up: {runner_up[0]} ({runner_up[1]:.1f} avg)")
            dashboard.append("")

    dashboard.append("### Overall Platform Rankings")
    dashboard.append("")

    for idx, (website, data_stats) in enumerate(sorted_websites, 1):
        avg = data_stats['average']
        dashboard.append(f"{idx}. **{website}: {avg:.1f}/7**")

    dashboard.append("")
    dashboard.append("### Coverage Summary")
    dashboard.append(f"- **Total Evaluations**: {sum(s['count'] for s in stats.values())} comparison analysis files")
    dashboard.append(f"- **Destinations**: {len(cities)} ({', '.join(cities)})")
    dashboard.append(f"- **Features**: {len(features)} evaluated")
    dashboard.append(f"- **Websites**: 4 compared")

    return "\n".join(dashboard)

if __name__ == "__main__":
    print("Scanning comparison analysis files...")
    data = scan_comparison_files()

    print("\nBuilding dashboard table...")
    table, cities, features, data = build_dashboard_table(data)

    print("\nCalculating statistics...")
    stats = calculate_statistics(data, cities, features)

    print("\nGenerating complete dashboard...")
    dashboard = generate_dashboard(data, table, cities, features, stats)

    # Write to file
    output_path = '/Users/yongqiwu/code/quality-check/quality_evaluation_output/travel_usability_dashboard.md'
    with open(output_path, 'w') as f:
        f.write(dashboard)

    print(f"\nDashboard written to: {output_path}")
    print(f"Total cities: {len(cities)}")
    print(f"Total features: {len(features)}")
    print(f"Total data points: {sum(s['count'] for s in stats.values())}")