import json
import os
import re
import requests
from pathlib import Path
from PIL import Image
import io
import unicodedata
import shutil
from urllib.parse import urlparse
import mimetypes


def get_file_extension(url):
    """Determine the correct file extension for a given URL."""
    # First try to get extension from URL
    parsed_url = urlparse(url)
    file_extension = os.path.splitext(parsed_url.path)[1].lower()
    
    if not file_extension:
        # Try to get extension from content type
        try:
            response = requests.head(url)
            content_type = response.headers.get('content-type', '').lower()
            if 'image/png' in content_type:
                file_extension = '.png'
            elif 'image/jpeg' in content_type or 'image/jpg' in content_type:
                file_extension = '.jpg'
            elif 'image/gif' in content_type:
                file_extension = '.gif'
            elif 'image/svg+xml' in content_type:
                file_extension = '.svg'
            elif 'image/webp' in content_type:
                file_extension = '.webp'
            else:
                # Default to .jpg for GitHub raw content
                if 'raw.githubusercontent.com' in url:
                    file_extension = '.jpg'
                else:
                    file_extension = '.png'
        except Exception as e:
            print(f"Error getting content type for {url}: {e}")
            # Default to .jpg for GitHub raw content
            if 'raw.githubusercontent.com' in url:
                file_extension = '.jpg'
            else:
                file_extension = '.png'
    
    return file_extension

def download_image(url, output_path):
    """Download an image from a URL and save it to the specified path."""
    try:
        headers = {
            'User-Agent': 'UniversityLogoHistoryWiki/1.0 (https://github.com/yourusername/university-logo-website; your@email.com) Python/3.x'
        }
        response = requests.get(url, stream=True, headers=headers)
        response.raise_for_status()
        
        # Get the file extension
        file_extension = get_file_extension(url)
        
        # Update output path with correct extension
        output_path = str(Path(output_path).with_suffix(file_extension))
        
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save the image
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return output_path
    except Exception as e:
        print(f"Error downloading image from {url}: {e}")
        return None

def load_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def sanitize_id(name):
    """Sanitize university name to create a consistent ID."""
    # Normalize unicode characters and convert to ASCII
    normalized = unicodedata.normalize('NFKD', name)
    ascii_name = normalized.encode('ascii', 'ignore').decode('ascii')
    # Convert to lowercase and replace spaces with hyphens
    return ascii_name.lower().replace(' ', '-')

def generate_university_page(university_id, university_data):
    """Generate HTML page for a university."""
    # Create images directory for this university
    images_dir = Path('images') / university_id
    images_dir.mkdir(parents=True, exist_ok=True)
    
    # Store downloaded image paths
    downloaded_images = {}
    
    # Download and store current logos of parent and predecessor institutions
    parent_logos = {}
    predecessor_logos = {}
    
    # Function to get current logo for an institution
    def get_current_logo(institution_id):
        try:
            institution_data = load_json_file(f'data/universities/{institution_id}.json')
            for logo in institution_data['logoHistory']:
                if logo.get('isCurrent', False):
                    return logo['imageUrl']
            # If no current logo is marked, use the first logo
            if institution_data['logoHistory']:
                return institution_data['logoHistory'][0]['imageUrl']
        except Exception as e:
            print(f"Error getting logo for {institution_id}: {e}")
        return None

    # Download and save images for regular logos
    for logo in university_data['logoHistory']:
        image_url = logo['imageUrl']
        # Get file extension
        file_extension = get_file_extension(image_url)
        
        # Create image filename using year
        image_filename = f"{logo['year']}{file_extension}"
        image_path = images_dir / image_filename
        
        # Download image if it doesn't exist
        if not image_path.exists():
            downloaded_path = download_image(image_url, str(image_path))
            if downloaded_path:
                downloaded_images[logo['year']] = downloaded_path
            else:
                # Use placeholder if download fails
                placeholder_path = Path('images/placeholder.png')
                if placeholder_path.exists():
                    shutil.copy(str(placeholder_path), str(image_path))
                    downloaded_images[logo['year']] = str(image_path)
        else:
            downloaded_images[logo['year']] = str(image_path)
    
    # Download and save images for special occasions
    for occasion in university_data.get('specialOccasions', []):
        image_url = occasion['imageUrl']
        # Get file extension
        file_extension = get_file_extension(image_url)
        
        # Create image filename using year and occasion
        image_filename = f"special_{occasion['year']}_{occasion['occasion'].lower().replace(' ', '_')}{file_extension}"
        image_path = images_dir / image_filename
        
        # Download image if it doesn't exist
        if not image_path.exists():
            downloaded_path = download_image(image_url, str(image_path))
            if downloaded_path:
                downloaded_images[f"special_{occasion['year']}"] = downloaded_path
            else:
                # Use placeholder if download fails
                placeholder_path = Path('images/placeholder.png')
                if placeholder_path.exists():
                    shutil.copy(str(placeholder_path), str(image_path))
                    downloaded_images[f"special_{occasion['year']}"] = str(image_path)
        else:
            downloaded_images[f"special_{occasion['year']}"] = str(image_path)
    
    # Sort logo history by year (newest first), handling estimated dates
    sorted_history = sorted(university_data['logoHistory'], 
                          key=lambda x: (int(x['year']), x.get('isEstimated', False)),
                          reverse=True)
    
    # Sort special occasions by year (newest first)
    sorted_occasions = sorted(university_data.get('specialOccasions', []),
                            key=lambda x: int(x['year']),
                            reverse=True)
    
    # Sort predecessors by year (newest first)
    sorted_predecessors = sorted(university_data.get('predecessors', []),
                               key=lambda x: int(x['year']),
                               reverse=True)

    # Sort parent institutions by year (newest first)
    sorted_parents = sorted(university_data.get('parentInstitutions', []),
                          key=lambda x: int(x['year']),
                          reverse=True)
    
    logo_entries = []
    for logo in sorted_history:
        estimated_mark = ' <span class="estimated-date">(estimated)</span>' if logo.get('isEstimated', False) else ''
        current_mark = ' <span class="current-logo">(Current)</span>' if logo.get('isCurrent', False) else ''
        
        # Get the image path relative to the root directory
        image_path = downloaded_images[logo['year']]
        relative_path = f"images/{university_id}/{Path(image_path).name}"
        
        logo_entries.append(f'''
            <div class="logo-entry">
                <a href="{relative_path}" target="_blank" class="logo-image-link">
                    <img src="{relative_path}" 
                         alt="{university_data['name']} logo from {logo['year']}" 
                         class="logo-image">
                </a>
                <div class="logo-details">
                    <h3>{logo['year']}{estimated_mark}{current_mark}</h3>
                    <p>{logo['description']}</p>
                    <a href="{logo['source']['url']}" 
                       target="_blank" 
                       class="source-link" 
                       rel="noopener noreferrer">
                        Source: {logo['source']['title']}
                    </a>
                </div>
            </div>
        ''')
    
    # Add special occasions section if there are any
    if sorted_occasions:
        logo_entries.append('<h2 class="special-occasions-title">Special Occasions</h2>')
        for occasion in sorted_occasions:
            current_mark = ' <span class="current-logo">(Current)</span>' if occasion.get('isCurrent', False) else ''
            
            # Get the image path relative to the root directory
            image_path = downloaded_images[f"special_{occasion['year']}"]
            relative_path = f"images/{university_id}/{Path(image_path).name}"
            
            logo_entries.append(f'''
                <div class="logo-entry special-occasion">
                    <a href="{relative_path}" target="_blank" class="logo-image-link">
                        <img src="{relative_path}" 
                             alt="{university_data['name']} {occasion['occasion']} logo from {occasion['year']}" 
                             class="logo-image">
                    </a>
                    <div class="logo-details">
                        <h3>{occasion['year']} - {occasion['occasion']}{current_mark}</h3>
                        <p>{occasion['description']}</p>
                        <a href="{occasion['source']['url']}" 
                           target="_blank" 
                           class="source-link" 
                           rel="noopener noreferrer">
                            Source: {occasion['source']['title']}
                        </a>
                    </div>
                </div>
            ''')

    # Add predecessors section if there are any
    predecessor_entries = []
    if sorted_predecessors:
        predecessor_entries.append('<h2 class="predecessors-title">Predecessor Universities</h2>')
        for predecessor in sorted_predecessors:
            # Check if predecessor university exists in our database
            predecessor_id = sanitize_id(predecessor['name'])
            predecessor_json_path = Path('data/universities') / f'{predecessor_id}.json'
            
            if predecessor_json_path.exists():
                # Get current logo for predecessor
                current_logo_url = get_current_logo(predecessor_id)
                if current_logo_url:
                    # Download and save the logo
                    file_extension = get_file_extension(current_logo_url)
                    image_filename = f"predecessor_{predecessor_id}{file_extension}"
                    image_path = images_dir / image_filename
                    
                    if not image_path.exists():
                        downloaded_path = download_image(current_logo_url, str(image_path))
                        if downloaded_path:
                            predecessor_logos[predecessor_id] = downloaded_path
                    else:
                        predecessor_logos[predecessor_id] = str(image_path)
                    
                    relative_path = f"images/{university_id}/{Path(predecessor_logos[predecessor_id]).name}"
                    
                    # Predecessor exists, create a link to its page with logo
                    predecessor_entries.append(f'''
                        <div class="predecessor-entry">
                            <div class="predecessor-info">
                                <h3>{predecessor['name']}</h3>
                                <p>Merged/Acquired: {predecessor['year']}</p>
                                <a href="universities/{predecessor_id}.html" class="predecessor-link">
                                    View Predecessor University →
                                </a>
                            </div>
                            <div class="predecessor-logo">
                                <a href="{relative_path}" target="_blank" class="logo-image-link">
                                    <img src="{relative_path}" 
                                         alt="Current logo of {predecessor['name']}" 
                                         class="logo-image">
                                </a>
                            </div>
                        </div>
                    ''')
                else:
                    # Predecessor exists but no logo found
                    predecessor_entries.append(f'''
                        <div class="predecessor-entry">
                            <div class="predecessor-info">
                                <h3>{predecessor['name']}</h3>
                                <p>Merged/Acquired: {predecessor['year']}</p>
                                <a href="universities/{predecessor_id}.html" class="predecessor-link">
                                    View Predecessor University →
                                </a>
                            </div>
                        </div>
                    ''')
            else:
                # Predecessor doesn't exist in our database
                predecessor_entries.append(f'''
                    <div class="predecessor-entry">
                        <div class="predecessor-info">
                            <h3>{predecessor['name']}</h3>
                            <p>Merged/Acquired: {predecessor['year']}</p>
                        </div>
                    </div>
                ''')

    # Add parent institutions section if there are any
    parent_entries = []
    if sorted_parents:
        parent_entries.append('<h2 class="parent-institutions-title">Parent Institutions</h2>')
        for parent in sorted_parents:
            # Check if parent institution exists in our database
            parent_id = sanitize_id(parent['name'])
            parent_json_path = Path('data/universities') / f'{parent_id}.json'
            
            if parent_json_path.exists():
                # Get current logo for parent
                current_logo_url = get_current_logo(parent_id)
                if current_logo_url:
                    # Download and save the logo
                    file_extension = get_file_extension(current_logo_url)
                    image_filename = f"parent_{parent_id}{file_extension}"
                    image_path = images_dir / image_filename
                    
                    if not image_path.exists():
                        downloaded_path = download_image(current_logo_url, str(image_path))
                        if downloaded_path:
                            parent_logos[parent_id] = downloaded_path
                    else:
                        parent_logos[parent_id] = str(image_path)
                    
                    relative_path = f"images/{university_id}/{Path(parent_logos[parent_id]).name}"
                    
                    # Parent exists, create a link to its page with logo
                    parent_entries.append(f'''
                        <div class="parent-institution-entry">
                            <div class="parent-info">
                                <h3>{parent['name']}</h3>
                                <p>Year: {parent['year']}</p>
                                <a href="universities/{parent_id}.html" class="parent-link">
                                    View Parent Institution →
                                </a>
                            </div>
                            <div class="parent-logo">
                                <a href="{relative_path}" target="_blank" class="logo-image-link">
                                    <img src="{relative_path}" 
                                         alt="Current logo of {parent['name']}" 
                                         class="logo-image">
                                </a>
                            </div>
                        </div>
                    ''')
                else:
                    # Parent exists but no logo found
                    parent_entries.append(f'''
                        <div class="parent-institution-entry">
                            <div class="parent-info">
                                <h3>{parent['name']}</h3>
                                <p>Year: {parent['year']}</p>
                                <a href="universities/{parent_id}.html" class="parent-link">
                                    View Parent Institution →
                                </a>
                            </div>
                        </div>
                    ''')
            else:
                # Parent doesn't exist in our database
                parent_entries.append(f'''
                    <div class="parent-institution-entry">
                        <div class="parent-info">
                            <h3>{parent['name']}</h3>
                            <p>Year: {parent['year']}</p>
                        </div>
                    </div>
                ''')

    page_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{university_data['name']} - Logo History</title>
    <link rel="stylesheet" href="styles.css">
    <link rel="stylesheet" href="university.css">
    <style>
        .predecessor-entry,
        .parent-institution-entry {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 2rem;
            padding: 1.5rem;
            background: #f8f9fa;
            border-radius: 8px;
            margin-bottom: 1rem;
        }}
        
        .predecessor-info,
        .parent-info {{
            flex: 1;
        }}
        
        .predecessor-logo,
        .parent-logo {{
            flex: 0 0 200px;
        }}
        
        .predecessor-logo img,
        .parent-logo img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
        }}
        
        @media (max-width: 768px) {{
            .predecessor-entry,
            .parent-institution-entry {{
                flex-direction: column;
                gap: 1rem;
            }}
            
            .predecessor-logo,
            .parent-logo {{
                flex: 0 0 auto;
                width: 100%;
                max-width: 200px;
                margin: 0 auto;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>{university_data['name']}</h1>
        <p>Logo History and Evolution</p>
    </header>

    <main class="university-page">
        <div class="navigation-buttons">
            <a href="index.html" class="nav-button">← Back to Universities</a>
            <a href="edit.html?id={university_id}" class="nav-button">Edit Entry</a>
        </div>

        <div class="university-info">
            <h2>University Information</h2>
            <div class="info-grid">
                <div class="info-item">
                    <h3>Location</h3>
                    <p>{university_data['location']['city']}, {university_data['location']['country']}</p>
                </div>
                <div class="info-item">
                    <h3>Founded</h3>
                    <p>{university_data['founded']}</p>
                </div>
            </div>
        </div>

        {''.join(parent_entries)}

        {''.join(predecessor_entries)}

        <div class="logo-history">
            <h2>Logo History</h2>
            {''.join(logo_entries)}
        </div>
    </main>

    <footer>
        <p>© 2024 University Logo History Wiki</p>
    </footer>
</body>
</html>'''

    # Write the page content to a file
    output_dir = Path('universities')
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f'{university_id}.html'
    output_file.write_text(page_content, encoding='utf-8')
    print(f'Generated page for {university_data["name"]}')

def update_index_json(universities_data):
    # Create index data with IDs based on university names
    index_data = {
        "universities": [
            {
                "id": uni["id"],
                "name": uni["name"],
                "location": uni["location"],
                "founded": uni["founded"]
            }
            for uni in universities_data
        ]
    }
    
    # Sort universities by name
    index_data["universities"].sort(key=lambda x: x["name"])
    
    # Save index.json
    save_json_file(index_data, "data/universities/index.json")
    print("Updated index.json")

def main():
    # Create necessary directories
    universities_dir = Path('universities')
    images_dir = Path('images')
    universities_dir.mkdir(exist_ok=True)
    images_dir.mkdir(exist_ok=True)
    
    # Get all JSON files from data/universities
    json_dir = Path('data/universities')
    universities_data = []
    
    for json_file in json_dir.glob('*.json'):
        if json_file.name == 'index.json':
            continue
            
        try:
            # Load university data
            university_data = load_json_file(json_file)
            
            # Use the sanitized ID from the JSON file
            university_id = university_data.get('id', sanitize_id(university_data['name']))
            
            # Save the updated JSON file
            save_json_file(university_data, json_file)
            
            universities_data.append(university_data)
            
            # Generate HTML
            generate_university_page(university_id, university_data)
            
        except Exception as e:
            print(f"Error processing {json_file.name}: {str(e)}")
    
    # Update index.json
    update_index_json(universities_data)

if __name__ == '__main__':
    main() 