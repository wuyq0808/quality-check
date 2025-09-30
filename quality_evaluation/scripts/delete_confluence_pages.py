#!/usr/bin/env python3
"""
Delete all child pages under a specified Confluence parent page

Usage:
    python3 delete_confluence_pages.py
"""

import os
import requests
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_child_pages(base_url, email, api_token, space_key, parent_page_id):
    """Get all child pages under a parent page"""
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    auth = (email, api_token)

    # Get child pages
    url = f"{base_url}/wiki/rest/api/content/{parent_page_id}/child/page"
    params = {
        'limit': 200,  # Increase limit to get more pages
        'expand': 'version'
    }

    all_pages = []

    while url:
        response = requests.get(url, headers=headers, auth=auth, params=params)

        if response.status_code != 200:
            logger.error(f"Failed to get child pages: {response.status_code} - {response.text}")
            return []

        data = response.json()
        pages = data.get('results', [])
        all_pages.extend(pages)

        logger.info(f"Found {len(pages)} pages in this batch, {len(all_pages)} total so far")

        # Check for next page
        if data.get('_links', {}).get('next'):
            url = base_url + "/wiki" + data['_links']['next']
            params = None  # Parameters are included in the next URL
        else:
            url = None

    return all_pages

def delete_page(base_url, email, api_token, page_id, page_title):
    """Delete a single page"""
    headers = {
        'Accept': 'application/json'
    }

    auth = (email, api_token)

    url = f"{base_url}/wiki/rest/api/content/{page_id}"

    response = requests.delete(url, headers=headers, auth=auth)

    if response.status_code in [204, 200]:
        logger.info(f"✅ Deleted page: {page_title} (ID: {page_id})")
        return True
    else:
        logger.error(f"❌ Failed to delete page {page_title} (ID: {page_id}): {response.status_code} - {response.text}")
        return False

def main():
    """Main function to delete all child pages"""
    load_dotenv("../../.env")

    # Configuration
    base_url = os.getenv('CONFLUENCE_BASE_URL', 'https://skyscanner.atlassian.net')
    email = os.getenv('CONFLUENCE_EMAIL', 'yongqi.wu@skyscanner.net')
    api_token = os.getenv('CONFLUENCE_API_TOKEN')
    space_key = os.getenv('CONFLUENCE_SPACE_KEY', '~yongqiwu')
    parent_page_id = "1424758076"  # Top Dest Check Local Runs

    if not api_token:
        logger.error("CONFLUENCE_API_TOKEN not found in environment variables")
        return

    logger.info(f"🔍 Finding all child pages under page ID: {parent_page_id}")

    # Get all child pages
    child_pages = get_child_pages(base_url, email, api_token, space_key, parent_page_id)

    if not child_pages:
        logger.info("No child pages found to delete")
        return

    logger.info(f"📋 Found {len(child_pages)} child pages to delete")

    # List all pages that will be deleted
    for page in child_pages:
        logger.info(f"  - {page['title']} (ID: {page['id']})")

    # Auto-confirm deletion
    logger.info(f"⚠️  Proceeding to delete ALL {len(child_pages)} pages...")

    # Delete all pages
    logger.info(f"🗑️  Starting deletion of {len(child_pages)} pages...")

    deleted_count = 0
    failed_count = 0

    for page in child_pages:
        if delete_page(base_url, email, api_token, page['id'], page['title']):
            deleted_count += 1
        else:
            failed_count += 1

    logger.info(f"🎉 Deletion complete!")
    logger.info(f"✅ Successfully deleted: {deleted_count} pages")
    if failed_count > 0:
        logger.info(f"❌ Failed to delete: {failed_count} pages")

if __name__ == "__main__":
    main()