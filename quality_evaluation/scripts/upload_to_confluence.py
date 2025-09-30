#!/usr/bin/env python3
"""
Upload All Files to Confluence

Comprehensive script to upload all markdown files from quality_evaluation_output
to Confluence with proper markdown conversion and flattened hierarchy using underscores.
"""

import os
import glob
import requests
import base64
import re
import logging
from pathlib import Path
from dotenv import load_dotenv
import markdown
from markdown.extensions import tables, fenced_code

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from environment"""
    load_dotenv(".env")

    config = {
        'base_url': os.getenv('CONFLUENCE_BASE_URL', 'https://skyscanner.atlassian.net'),
        'email': os.getenv('CONFLUENCE_EMAIL'),
        'token': os.getenv('CONFLUENCE_API_TOKEN'),
        'space_key': os.getenv('CONFLUENCE_SPACE_KEY', '~yongqiwu'),
        'parent_id': os.getenv('CONFLUENCE_PARENT_PAGE_ID', '1424758076')
    }

    if not config['email'] or not config['token']:
        raise ValueError("CONFLUENCE_EMAIL and CONFLUENCE_API_TOKEN must be set in .env file")

    return config

def create_auth_headers(email, token):
    """Create authentication headers for Confluence API"""
    auth_string = f"{email}:{token}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()

    return {
        'Authorization': f'Basic {encoded_auth}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

def create_flat_title(file_path, output_dir):
    """Create flat titles using underscores and remove timestamps"""
    rel_path = os.path.relpath(file_path, output_dir)
    path_parts = rel_path.split(os.sep)
    filename = os.path.splitext(path_parts[-1])[0]  # Remove .md extension

    # Remove timestamp patterns (YYYYMMDD_HHMMSS format)
    # Pattern 1: suffix like "file_20250927_095959"
    filename = re.sub(r'_\d{8}_\d{6}$', '', filename)
    # Pattern 2: entire filename is timestamp like "20250927_095959"
    if re.match(r'^\d{8}_\d{6}$', filename):
        filename = ''  # Empty for timestamp-only files

    # Create flat title with path parts
    if len(path_parts) > 1:
        # Don't include the filename if it's empty (was just a timestamp)
        if filename:
            title_parts = path_parts[:-1] + [filename]
        else:
            title_parts = path_parts[:-1]
    else:
        title_parts = [filename] if filename else ['file']

    return "_".join(title_parts)

def convert_markdown_to_confluence(markdown_content):
    """Convert markdown to Confluence storage format"""

    # Initialize markdown processor with extensions
    md = markdown.Markdown(
        extensions=[
            'tables',
            'fenced_code',
            'nl2br',
            'attr_list'
        ],
        extension_configs={
            'tables': {},
            'fenced_code': {},
        }
    )

    # Convert markdown to HTML
    html = md.convert(markdown_content)

    # Convert HTML links to Confluence link format
    html = convert_links_to_confluence(html)

    # Convert HTML tables to Confluence format
    html = convert_tables_to_confluence(html)

    # Convert headers to Confluence format
    html = convert_headers_to_confluence(html)

    # Convert code blocks to Confluence format
    html = convert_code_blocks_to_confluence(html)

    # Clean up HTML for Confluence storage format
    html = clean_html_for_confluence(html)

    return html

def convert_links_to_confluence(html):
    """Convert HTML links to Confluence link format"""

    # Convert <a href="url">text</a> to <a href="url">text</a> (Confluence format)
    # Confluence uses standard HTML <a> tags for external links
    html = re.sub(
        r'<a href="([^"]+)">([^<]+)</a>',
        r'<a href="\1">\2</a>',
        html
    )

    return html

def convert_tables_to_confluence(html):
    """Convert HTML tables to Confluence table format"""

    # Replace table tags
    html = html.replace('<table>', '<table data-layout="default" ac:local-id="table1">')
    html = html.replace('</table>', '</table>')

    # Convert thead/tbody structure
    html = re.sub(r'<thead>(.*?)</thead>', r'\1', html, flags=re.DOTALL)
    html = re.sub(r'<tbody>(.*?)</tbody>', r'\1', html, flags=re.DOTALL)

    # Convert th to td with header styling
    html = re.sub(r'<th>(.*?)</th>', r'<th><p><strong>\1</strong></p></th>', html)

    # Wrap td content in paragraphs
    # First handle cells that contain links - wrap them in <p>
    html = re.sub(r'<td>(<a[^>]*>.*?</a>)</td>', r'<td><p>\1</p></td>', html)
    # Then handle cells without links
    html = re.sub(r'<td>([^<][^>]*?)</td>', r'<td><p>\1</p></td>', html)

    return html

def convert_headers_to_confluence(html):
    """Convert HTML headers to Confluence format"""

    # Convert h1-h6 to Confluence headers
    for i in range(1, 7):
        html = re.sub(
            f'<h{i}>(.*?)</h{i}>',
            f'<h{i}><strong>\\1</strong></h{i}>',
            html
        )

    return html

def convert_code_blocks_to_confluence(html):
    """Convert code blocks to Confluence code macro"""

    # Convert fenced code blocks
    html = re.sub(
        r'<pre><code class="language-(\w+)">(.*?)</code></pre>',
        r'<ac:structured-macro ac:name="code" ac:schema-version="1"><ac:parameter ac:name="language">\1</ac:parameter><ac:plain-text-body><![CDATA[\2]]></ac:plain-text-body></ac:structured-macro>',
        html,
        flags=re.DOTALL
    )

    # Convert regular code blocks
    html = re.sub(
        r'<pre><code>(.*?)</code></pre>',
        r'<ac:structured-macro ac:name="code" ac:schema-version="1"><ac:plain-text-body><![CDATA[\1]]></ac:plain-text-body></ac:structured-macro>',
        html,
        flags=re.DOTALL
    )

    # Convert inline code
    html = re.sub(r'<code>(.*?)</code>', r'<code>\1</code>', html)

    return html

def clean_html_for_confluence(html):
    """Clean HTML for Confluence storage format"""

    # Ensure paragraphs are properly formatted
    html = re.sub(r'<p>\s*</p>', '', html)  # Remove empty paragraphs
    html = re.sub(r'<br\s*/?>', '<br/>', html)  # Normalize br tags

    # Wrap bare text in paragraphs
    lines = html.split('\n')
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if line and not line.startswith('<') and not line.endswith('>'):
            line = f'<p>{line}</p>'
        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)

def find_all_markdown_files(output_dir):
    """Find all markdown files in the output directory"""
    pattern = os.path.join(output_dir, "**", "*.md")
    md_files = glob.glob(pattern, recursive=True)

    # Filter out README files
    content_files = [f for f in md_files if os.path.basename(f) != "README.md"]

    logger.info(f"Found {len(content_files)} markdown files to upload")
    return content_files

def check_page_exists(headers, base_url, space_key, title):
    """Check if a page with the given title already exists"""

    search_url = f"{base_url}/wiki/rest/api/content"
    search_params = {
        'title': title,
        'spaceKey': space_key,
        'type': 'page',
        'expand': 'version'
    }

    try:
        response = requests.get(search_url, headers=headers, params=search_params, timeout=10)
        if response.status_code == 200:
            results = response.json().get('results', [])
            return results[0] if results else None
        else:
            logger.warning(f"Search failed for '{title}': {response.status_code}")
            return None
    except Exception as e:
        logger.warning(f"Search error for '{title}': {e}")
        return None

def upload_page(headers, base_url, space_key, parent_id, title, html_content):
    """Upload or update a page in Confluence"""

    # Check if page exists
    existing_page = check_page_exists(headers, base_url, space_key, title)

    page_data = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "ancestors": [{"id": parent_id}],
        "body": {
            "storage": {
                "value": html_content,
                "representation": "storage"
            }
        }
    }

    try:
        if existing_page:
            # Update existing page
            page_id = existing_page['id']
            version = existing_page['version']['number']
            page_data['version'] = {'number': version + 1}

            response = requests.put(
                f"{base_url}/wiki/rest/api/content/{page_id}",
                headers=headers,
                json=page_data,
                timeout=30
            )

            action = "Updated"
        else:
            # Create new page
            response = requests.post(
                f"{base_url}/wiki/rest/api/content",
                headers=headers,
                json=page_data,
                timeout=30
            )

            action = "Created"

        if response.status_code == 200:
            page_info = response.json()
            page_url = f"{base_url}/wiki{page_info.get('_links', {}).get('webui', '')}"
            logger.info(f"✅ {action}: {title}")
            logger.info(f"   URL: {page_url}")
            return True
        else:
            logger.error(f"❌ Failed to upload '{title}': {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"❌ Upload error for '{title}': {e}")
        return False

def check_parent_page(headers, base_url, parent_id):
    """Check parent page details and return its space"""
    try:
        response = requests.get(
            f"{base_url}/wiki/rest/api/content/{parent_id}",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            page_info = response.json()
            space_key = page_info.get('space', {}).get('key')
            logger.info(f"✅ Parent page found: {page_info.get('title')}")
            logger.info(f"   Space: {space_key}")
            logger.info(f"   ID: {page_info.get('id')}")
            return space_key
        else:
            logger.error(f"❌ Parent page check failed: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"❌ Parent page check error: {e}")
        return None

def main():
    """Main function to upload all files or specific files"""

    import sys
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Upload markdown files to Confluence',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Upload specific file
  python upload_to_confluence.py travel_usability_dashboard.md

  # Upload multiple files
  python upload_to_confluence.py file1.md file2.md

  # Upload with relative paths
  python upload_to_confluence.py comparison_analysis/autocomplete_for_destinations_hotels/London/comparison.md

  # Upload latest versions from find_latest_versions.py
  python find_latest_versions.py --output-paths | xargs python upload_to_confluence.py
        '''
    )
    parser.add_argument('files', nargs='+', help='Files to upload (relative to quality_evaluation_output). Required.')

    args = parser.parse_args()

    logger.info(f"🚀 Starting Confluence upload for {len(args.files)} file(s)...")

    try:
        # Load configuration
        config = load_config()
        headers = create_auth_headers(config['email'], config['token'])

        # Use the configured space directly instead of checking parent
        actual_space = config['space_key']
        logger.info(f"Using configured space: {actual_space}")

        # Verify parent page exists in this space
        parent_info = check_parent_page(headers, config['base_url'], config['parent_id'])
        if not parent_info:
            logger.error("Cannot access parent page")
            return

        # Find output directory
        output_dir = "../../quality_evaluation_output"
        if not os.path.exists(output_dir):
            logger.error(f"Output directory '{output_dir}' not found!")
            return

        # Use specific files provided (required)
        md_files = []
        for file_arg in args.files:
            # Try as absolute path first
            if os.path.isabs(file_arg) and os.path.exists(file_arg):
                md_files.append(file_arg)
            else:
                # Try relative to output_dir
                full_path = os.path.join(output_dir, file_arg)
                if os.path.exists(full_path):
                    md_files.append(full_path)
                else:
                    logger.error(f"❌ File not found: {file_arg}")
                    logger.error(f"   Tried: {full_path}")
                    return

        logger.info(f"📂 Uploading {len(md_files)} file(s)")

        logger.info(f"🎯 Target: {config['base_url']}/wiki/spaces/{actual_space}")

        # Process each file
        successful_uploads = 0
        failed_uploads = 0

        for file_path in md_files:
            try:
                # Create flat title
                title = create_flat_title(file_path, output_dir)

                # Read markdown content
                with open(file_path, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()

                # Skip empty files
                if not markdown_content.strip():
                    logger.warning(f"⚠️  Skipping empty file: {title}")
                    continue

                # Convert markdown to Confluence format
                html_content = convert_markdown_to_confluence(markdown_content)

                # Upload to Confluence using actual space
                if upload_page(headers, config['base_url'], actual_space,
                             config['parent_id'], title, html_content):
                    successful_uploads += 1
                else:
                    failed_uploads += 1

            except Exception as e:
                logger.error(f"❌ Error processing '{file_path}': {e}")
                failed_uploads += 1

        # Summary
        logger.info(f"🎉 Upload complete!")
        logger.info(f"   ✅ Successful: {successful_uploads}")
        logger.info(f"   ❌ Failed: {failed_uploads}")
        logger.info(f"   📊 Total: {len(md_files)}")

        if successful_uploads > 0:
            logger.info(f"🔗 View all pages: {config['base_url']}/wiki/spaces/{actual_space}")

    except Exception as e:
        logger.error(f"💥 Upload process failed: {e}")

if __name__ == "__main__":
    main()