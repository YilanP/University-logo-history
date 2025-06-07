// Cache for storing university data
let universitiesCache = null;
let selectedCountry = null;

// Debounce function to limit how often a function can be called
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Format location string
function formatLocation(location) {
    return `${location.city}, ${location.country}`;
}

// Get unique countries from universities
function getUniqueCountries(universities) {
    return [...new Set(universities.map(u => u.location.country))].sort();
}

// Create country filter
function createCountryFilter(universities) {
    const countries = getUniqueCountries(universities);
    const filterContainer = document.createElement('div');
    filterContainer.className = 'country-filter';
    
    const select = document.createElement('select');
    select.id = 'countryFilter';
    
    // Add "All Countries" option
    const allOption = document.createElement('option');
    allOption.value = '';
    allOption.textContent = 'All Countries';
    select.appendChild(allOption);
    
    // Add country options
    countries.forEach(country => {
        const option = document.createElement('option');
        option.value = country;
        option.textContent = country;
        select.appendChild(option);
    });
    
    filterContainer.appendChild(select);
    return filterContainer;
}

// Filter and display universities based on search and country filter
function filterAndDisplayUniversities() {
    if (!universitiesCache) return;
    
    const searchInput = document.querySelector('.search-input');
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    const countryFilter = document.getElementById('countryFilter');
    const selectedCountry = countryFilter ? countryFilter.value : '';
    
    const filteredUniversities = universitiesCache.filter(university => {
        const matchesSearch = 
            university.name.toLowerCase().includes(searchTerm) ||
            university.location.city.toLowerCase().includes(searchTerm) ||
            university.location.country.toLowerCase().includes(searchTerm);
        
        const matchesCountry = !selectedCountry || university.location.country === selectedCountry;
        
        return matchesSearch && matchesCountry;
    });
    
    displayUniversities(filteredUniversities);
}

// Fetch and display universities
async function loadUniversities() {
    const grid = document.getElementById('universitiesGrid');
    if (!grid) return;
    
    // Show loading state
    grid.innerHTML = '<div class="loading">Loading universities...</div>';
    
    try {
        const response = await fetch('data/universities/index.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        universitiesCache = data.universities;
        
        // Create search container
        const searchContainer = document.createElement('div');
        searchContainer.className = 'search-container';
        
        // Create search input
        const searchInput = document.createElement('input');
        searchInput.type = 'text';
        searchInput.placeholder = 'Search universities...';
        searchInput.className = 'search-input';
        searchContainer.appendChild(searchInput);
        
        // Create country filter
        const countryFilter = createCountryFilter(universitiesCache);
        searchContainer.appendChild(countryFilter);
        
        // Add search container to main
        const main = document.querySelector('main');
        main.insertBefore(searchContainer, main.firstChild);
        
        // Display universities
        displayUniversities(universitiesCache);
        
        // Setup search functionality
        searchInput.addEventListener('input', debounce(filterAndDisplayUniversities, 300));
        
        // Setup country filter
        countryFilter.querySelector('select').addEventListener('change', filterAndDisplayUniversities);
    } catch (error) {
        console.error('Error loading universities:', error);
        const main = document.querySelector('main');
        main.innerHTML = `
            <div class="error-container">
                <h2>Error Loading Universities</h2>
                <p>There was a problem loading the university data. Please try again later.</p>
                <button onclick="location.reload()" class="retry-button">Retry</button>
            </div>
        `;
    }
}


// Get current logo from university data
async function getCurrentLogo(universityId) {
    try {
        const response = await fetch(`data/universities/${universityId}.json`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const university = await response.json();
        const sortedHistory = [...university.logoHistory].sort((a, b) => {
            const yearA = parseInt(a.year);
            const yearB = parseInt(b.year);
            if (yearA === yearB) {
                return a.isEstimated ? 1 : -1;
            }
            return yearB - yearA;  // Sort in descending order (newest first)
        });
        return sortedHistory[0]?.imageUrl || 'images/placeholder.png';
    } catch (error) {
        console.error(`Error getting current logo for ${universityId}:`, error);
        return 'images/placeholder.png';
    }
}

// Display universities in the grid
async function displayUniversities(universities) {
    const grid = document.getElementById('universitiesGrid');
    if (!grid) return;
    
    // Create a document fragment to batch DOM updates
    const fragment = document.createDocumentFragment();
    
    for (const university of universities) {
        const card = document.createElement('div');
        card.className = 'university-card';
        const universityId = university.id;
        card.onclick = () => window.location.href = `universities/${universityId}.html`;
        
        const currentLogo = await getCurrentLogo(universityId);
        
        card.innerHTML = `
            <img src="${currentLogo}" alt="${university.name} logo" onerror="this.src='images/placeholder.png'">
            <div class="university-card-content">
                <h2>${university.name}</h2>
                <p>Founded: ${university.founded}</p>
                <p>${formatLocation(university.location)}</p>
            </div>
        `;
        
        fragment.appendChild(card);
    }
    
    // Clear and update the grid in one operation
    grid.innerHTML = '';
    grid.appendChild(fragment);
}

// Load universities when the page loads
document.addEventListener('DOMContentLoaded', loadUniversities);

// Generate university page
async function generateUniversityPage(universityId) {
    try {
        const response = await fetch(`data/universities/${universityId}.json`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const university = await response.json();

        // Sort logo history by year, handling estimated dates
        const sortedHistory = [...university.logoHistory].sort((a, b) => {
            const yearA = parseInt(a.year);
            const yearB = parseInt(b.year);
            if (yearA === yearB) {
                return a.isEstimated ? 1 : -1;
            }
            return yearB - yearA;
        });

        const logoEntries = sortedHistory.map(logo => `
            <div class="logo-entry">
                <img src="${logo.imageUrl}" 
                     alt="${university.name} logo from ${logo.year}" 
                     class="logo-image">
                <div class="logo-details">
                    <h3>${logo.year} ${logo.isEstimated ? '<span class="estimated-date">(estimated)</span>' : ''} ${logo.isCurrent ? '<span class="current-logo">(Current)</span>' : ''}</h3>
                    <p>${logo.description}</p>
                    <a href="${logo.source.url}" 
                       target="_blank" 
                       class="source-link" 
                       rel="noopener noreferrer">
                        Source: ${logo.source.title}
                    </a>
                </div>
            </div>
        `).join('');

        const pageContent = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${university.name} - Logo History</title>
    <link rel="stylesheet" href="../styles.css">
    <link rel="stylesheet" href="../university.css">
</head>
<body>
    <header>
        <h1>${university.name}</h1>
        <p>Logo History and Evolution</p>
    </header>

    <main class="university-page">
        <div class="navigation-buttons">
            <a href="../index.html" class="nav-button">← Back to Universities</a>
            <a href="../edit.html?id=${universityId}" class="nav-button">Edit Entry</a>
        </div>

        <div class="university-info">
            <h2>University Information</h2>
            <div class="info-grid">
                <div class="info-item">
                    <h3>Location</h3>
                    <p>${university.location.city}, ${university.location.country}</p>
                </div>
                <div class="info-item">
                    <h3>Founded</h3>
                    <p>${university.founded}</p>
                </div>
            </div>
        </div>

        <div class="logo-history">
            <h2>Logo History</h2>
            ${logoEntries}
        </div>
    </main>

    <footer>
        <p>© 2024 University Logo History Wiki</p>
    </footer>
</body>
</html>`;

        // Write the page content to a file
        const fs = require('fs');
        const path = require('path');
        const outputDir = path.join(__dirname, 'universities');
        
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }
        
        fs.writeFileSync(path.join(outputDir, `${universityId}.html`), pageContent);
        console.log(`Generated page for ${university.name}`);
    } catch (error) {
        console.error(`Error generating page for ${universityId}:`, error);
    }
} 