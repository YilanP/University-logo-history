import json
import os
import re
import requests
from pathlib import Path
from PIL import Image
import io
import unicodedata
import shutil


def download_image(url, output_path):
    try:
        # Set up headers with User-Agent
        headers = {
            'User-Agent': 'University Logo History Wiki Bot/1.0 (https://github.com/yourusername/university-logo-website; your@email.com)'
        }
        
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save the image in its original format
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Successfully downloaded image to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error downloading image from {url}: {str(e)}")
        return False

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
    # Sort logo history by year (newest first), handling estimated dates
    sorted_history = sorted(university_data['logoHistory'], 
                          key=lambda x: (int(x['year']), x.get('isEstimated', False)),
                          reverse=True)  # Add reverse=True to sort newest first
    
    logo_entries = []
    for logo in sorted_history:
        estimated_mark = ' <span class="estimated-date">(estimated)</span>' if logo.get('isEstimated', False) else ''
        current_mark = ' <span class="current-logo">(Current)</span>' if logo.get('isCurrent', False) else ''
        logo_entries.append(f'''
            <div class="logo-entry">
                <img src="{logo['imageUrl']}" 
                     alt="{university_data['name']} logo from {logo['year']}" 
                     class="logo-image">
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

    page_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{university_data['name']} - Logo History</title>
    <link rel="stylesheet" href="../styles.css">
    <link rel="stylesheet" href="../university.css">
</head>
<body>
    <header>
        <h1>{university_data['name']}</h1>
        <p>Logo History and Evolution</p>
    </header>

    <main class="university-page">
        <div class="navigation-buttons">
            <a href="../index.html" class="nav-button">← Back to Universities</a>
            <a href="../edit.html?id={university_id}" class="nav-button">Edit Entry</a>
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