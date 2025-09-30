#!/usr/bin/env python3
"""
Check Page Content

Script to fetch and display the actual HTML content from Confluence page.
"""

import os
import requests
import base64
from dotenv import load_dotenv

def check_page_content():
    """Fetch and display page content"""

    load_dotenv(".env")

    base_url = os.getenv('CONFLUENCE_BASE_URL', 'https://skyscanner.atlassian.net')
    email = os.getenv('CONFLUENCE_EMAIL')
    token = os.getenv('CONFLUENCE_API_TOKEN')
    page_id = '1469744109'  # travel_usability_dashboard

    # Setup auth
    auth_string = f"{email}:{token}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()

    headers = {
        'Authorization': f'Basic {encoded_auth}',
        'Accept': 'application/json'
    }

    print(f"🔍 Fetching page content for: {page_id}")

    try:
        # Get page content with storage format
        url = f"{base_url}/wiki/rest/api/content/{page_id}"
        params = {
            'expand': 'body.storage'
        }

        response = requests.get(url, headers=headers, params=params, timeout=15)

        if response.status_code != 200:
            print(f"❌ Failed to get page: {response.status_code}")
            return

        data = response.json()
        storage_content = data.get('body', {}).get('storage', {}).get('value', '')

        print(f"\n📄 Page Title: {data.get('title')}")
        print(f"\n📝 Storage Format Content (first 2000 chars):")
        print("=" * 80)
        print(storage_content[:2000])
        print("=" * 80)

        # Look for link patterns in the content
        print("\n🔗 Searching for link patterns...")
        import re
        links = re.findall(r'<a[^>]*>.*?</a>', storage_content[:2000])
        if links:
            print(f"Found {len(links)} links:")
            for i, link in enumerate(links[:5], 1):
                print(f"  {i}. {link}")
        else:
            print("No <a> tags found")

        # Look for paragraph content in table cells
        print("\n📊 Searching for table cell content...")
        cells = re.findall(r'<td><p>.*?</p></td>', storage_content[:2000])
        if cells:
            print(f"Found {len(cells)} table cells:")
            for i, cell in enumerate(cells[:5], 1):
                print(f"  {i}. {cell}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_page_content()