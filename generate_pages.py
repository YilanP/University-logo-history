import json
import os
import re
import requests
from pathlib import Path
from PIL import Image
import io
import unicodedata

def sanitize_filename(name):
    # Convert to lowercase and replace spaces with hyphens
    sanitized = name.lower().replace(' ', '-')
    # Remove any characters that aren't alphanumeric or hyphens
    sanitized = ''.join(c for c in sanitized if c.isalnum() or c == '-')
    return sanitized

def download_image(url, save_path):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Check if it's an SVG file
        if url.lower().endswith('.svg') or 'svg' in response.headers.get('content-type', '').lower():
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
            
        # For other image types, verify with PIL
        img = Image.open(io.BytesIO(response.content))
        img.save(save_path)
        return True
    except Exception as e:
        print(f"Error downloading image {url}: {str(e)}")
        return False

def load_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def generate_university_page(university_data, output_dir):
    # Use university name as ID
    university_id = sanitize_filename(university_data['name'])
    
    # Create images directory for this university
    images_dir = os.path.join('images', university_id)
    os.makedirs(images_dir, exist_ok=True)
    
    # Download and save images
    for logo in university_data['logoHistory']:
        image_path = os.path.join(images_dir, f"{logo['year']}.png")
        if not os.path.exists(image_path):
            if not download_image(logo['source']['url'], image_path):
                print(f"Failed to download image for {university_data['name']} - {logo['year']}")
    
    # Generate HTML content
    html_content = f"""<!DOCTYPE html>
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
            {generate_logo_history_html(university_data)}
        </div>
    </main>

    <footer>
        <p>© 2024 University Logo History Wiki</p>
    </footer>
</body>
</html>"""
    
    # Save HTML file
    output_path = os.path.join(output_dir, f"{university_id}.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Generated {output_path}")

def generate_logo_history_html(university_data):
    # Sort logo history by year (newest first)
    logo_history = sorted(university_data['logoHistory'], key=lambda x: x['year'], reverse=True)
    
    # Generate HTML for each logo entry
    logo_entries = []
    for logo in logo_history:
        university_id = sanitize_filename(university_data['name'])
        estimated_html = '<span class="estimated-date">(estimated)</span>' if logo.get('isEstimated') else ''
        
        entry = f"""
            <div class="logo-entry">
                <img src="../images/{university_id}/{logo['year']}.png" 
                     alt="{university_data['name']} logo from {logo['year']}" 
                     class="logo-image">
                <div class="logo-details">
                    <h3>{logo['year']} {estimated_html}</h3>
                    <p>{logo['description']}</p>
                    <a href="{logo['source']['url']}" 
                       target="_blank" 
                       class="source-link" 
                       rel="noopener noreferrer">
                        Source: {logo['source']['title']}
                    </a>
                </div>
            </div>
        """
        logo_entries.append(entry)
    
    return '\n'.join(logo_entries)

def update_index_json(universities_data):
    # Create index data with IDs based on university names
    index_data = {
        "universities": [
            {
                "id": sanitize_filename(uni["name"]),
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
            
            # Update the ID to be based on the university name
            university_data['id'] = sanitize_filename(university_data['name'])
            
            # Save the updated JSON file
            save_json_file(university_data, json_file)
            
            universities_data.append(university_data)
            
            # Generate HTML
            generate_university_page(university_data, universities_dir)
            
        except Exception as e:
            print(f"Error processing {json_file.name}: {str(e)}")
    
    # Update index.json
    update_index_json(universities_data)

if __name__ == '__main__':
    main() 