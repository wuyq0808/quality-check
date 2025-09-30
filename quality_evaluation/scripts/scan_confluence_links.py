#!/usr/bin/env python3
"""
Scan Confluence Links

Script to scan all pages in the Confluence space and categorize them.
"""

import os
import requests
import base64
from dotenv import load_dotenv
from collections import defaultdict

def scan_confluence_pages():
    """Scan all pages in the Confluence space and return link mapping"""

    load_dotenv(".env")

    base_url = os.getenv('CONFLUENCE_BASE_URL', 'https://skyscanner.atlassian.net')
    email = os.getenv('CONFLUENCE_EMAIL')
    token = os.getenv('CONFLUENCE_API_TOKEN')
    space_key = os.getenv('CONFLUENCE_SPACE_KEY', '~yongqiwu')
    parent_id = os.getenv('CONFLUENCE_PARENT_PAGE_ID', '1424758076')

    # Setup auth
    auth_string = f"{email}:{token}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()

    headers = {
        'Authorization': f'Basic {encoded_auth}',
        'Accept': 'application/json'
    }

    print(f"🔍 Scanning all pages in space: {space_key}")
    print(f"   Under parent: {parent_id}")
    print()

    try:
        # Get all child pages under parent
        url = f"{base_url}/wiki/rest/api/content/{parent_id}/child/page"
        params = {
            'limit': 500,
            'expand': 'version'
        }

        all_pages = []
        page_count = 0

        while url:
            response = requests.get(url, headers=headers, params=params, timeout=15)

            if response.status_code != 200:
                print(f"❌ Failed to get pages: {response.status_code}")
                return None

            data = response.json()
            pages = data.get('results', [])
            all_pages.extend(pages)
            page_count += len(pages)

            print(f"   📄 Retrieved {len(pages)} pages (total: {page_count})")

            # Check for next page
            next_link = data.get('_links', {}).get('next')
            if next_link:
                url = f"{base_url}{next_link}"
                params = {}
            else:
                url = None

        print(f"\n📊 Total pages found: {len(all_pages)}")
        print()

        # Build mapping for comparison analysis pages
        # Format: {city: {feature: page_id}}
        comparison_links = defaultdict(dict)

        # Feature name mapping
        feature_map = {
            'autocomplete_for_destinations_hotels': 'autocomplete',
            'relevance_of_top_listings': 'relevance',
            'five_partners_per_hotel': 'five_partners',
            'hero_position_partner_mix': 'hero_pos',
            'distance_accuracy': 'distance'
        }

        # Cities to track
        cities = ['Tokyo', 'London', 'Paris', 'Barcelona', 'Dubai', 'Rome']

        for page in all_pages:
            title = page['title']
            page_id = page['id']

            # Only process comparison_analysis pages
            if 'comparison_analysis' not in title:
                continue

            # Extract city and feature from title
            # Format: comparison_analysis_<feature>_<city>
            for feature_full, feature_short in feature_map.items():
                if feature_full in title:
                    for city in cities:
                        if city in title:
                            page_url = f"{base_url}/wiki/spaces/{space_key}/pages/{page_id}"
                            comparison_links[city][feature_short] = page_url
                            print(f"   🔗 Mapped: {city} - {feature_short} -> {page_id}")
                            break
                    break

        print(f"\n✅ Found {sum(len(v) for v in comparison_links.values())} comparison links")
        return comparison_links

    except Exception as e:
        print(f"❌ Error scanning pages: {e}")
        return None

if __name__ == "__main__":
    scan_confluence_pages()