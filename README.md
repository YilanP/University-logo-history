# University Logo History Wiki

A static website showcasing the evolution of university logos through time. Built with plain HTML, CSS, and JavaScript.

## Features

- Responsive grid layout of universities
- Search functionality to filter universities
- Individual pages for each university showing logo evolution
- Clean and modern design
- Mobile-friendly interface

## Project Structure

```
university-logo-website/
├── index.html              # Main page listing all universities
├── styles.css             # Main stylesheet
├── script.js              # Main JavaScript file
├── data/
│   └── universities.json  # University data in JSON format
├── universities/          # Individual university pages
│   └── harvard.html      # Example university page
└── images/               # Image assets
    ├── placeholder.svg   # Placeholder for missing logos
    ├── harvard/         # Harvard logo images
    └── oxford/          # Oxford logo images
```

## Setup

1. Clone this repository
2. Add your university logo images to the `images` directory
3. Update the `data/universities.json` file with your university data
4. Create individual university pages in the `universities` directory following the template

## Adding a New University

1. Add the university data to `data/universities.json`
2. Create a new HTML file in the `universities` directory (e.g., `universities/your-university.html`)
3. Copy the template from `harvard.html` and update the content
4. Add the university's logo images to the `images` directory

## Data Format

The `universities.json` file follows this structure:

```json
{
    "universities": [
        {
            "id": "unique-id",
            "name": "University Name",
            "location": "City, Country",
            "founded": 1234,
            "currentLogo": "images/path/to/current.png",
            "logoHistory": [
                {
                    "year": 1234,
                    "description": "Description of the logo",
                    "image": "images/path/to/logo.png"
                }
            ]
        }
    ]
}
```

## Contributing

Feel free to contribute by:
1. Adding more universities
2. Improving the design
3. Adding new features
4. Fixing bugs

## License

This project is open source and available under the MIT License. 