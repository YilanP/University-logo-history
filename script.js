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
        const sortedHistory = [...university.logoHistory].sort((a, b) => b.year - a.year);
        return sortedHistory[0]?.image || 'images/placeholder.png';
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
        card.onclick = () => window.location.href = `universities/${university.id}.html`;
        
        const currentLogo = await getCurrentLogo(university.id);
        
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