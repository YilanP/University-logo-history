import json
import os
import re
import requests
from pathlib import Path
from PIL import Image
import io
import unicodedata
import shutil

def sanitize_filename(name):
    # Convert to lowercase and replace spaces with hyphens
    sanitized = name.lower().replace(' ', '-')
    # Remove any characters that aren't alphanumeric or hyphens
    sanitized = ''.join(c for c in sanitized if c.isalnum() or c == '-')
    return sanitized

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

def generate_university_page(university_data, output_dir):
    # Use university name as ID
    university_id = sanitize_filename(university_data['name'])
    
    # Create images directory for this university
    images_dir = os.path.join('images', university_id)
    os.makedirs(images_dir, exist_ok=True)
    
    # Download and save images
    for logo in university_data['logoHistory']:
        # Get the original file extension from the URL
        image_url = logo['imageUrl']
        file_extension = os.path.splitext(image_url.split('/')[-1])[1]
        if not file_extension:
            file_extension = '.png'  # Default to .png if no extension found
        
        # Create a filename based on the year with original extension
        image_filename = f"{logo['year']}{file_extension}"
        image_path = os.path.join(images_dir, image_filename)
        
        # Only download if the image doesn't exist
        if not os.path.exists(image_path):
            if not download_image(logo['imageUrl'], image_path):
                print(f"Failed to download image for {university_data['name']} - {logo['year']}")
                # Create a placeholder image if download fails
                placeholder_path = os.path.join('images', 'placeholder.png')
                if os.path.exists(placeholder_path):
                    shutil.copy(placeholder_path, image_path)
    
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
        
        # Get the original file extension from the URL
        image_url = logo['imageUrl']
        file_extension = os.path.splitext(image_url.split('/')[-1])[1]
        if not file_extension:
            file_extension = '.png'  # Default to .png if no extension found
        
        entry = f"""
            <div class="logo-entry">
                <img src="../images/{university_id}/{logo['year']}{file_extension}" 
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