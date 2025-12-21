/**
 * Duc Tran Portfolio - JavaScript
 * Fetches GitHub repos and displays them dynamically
 */

const GITHUB_USERNAME = 'ductran27';
const FEATURED_REPOS = [
    'LIS-landsurface-toolkit',
    'NOAA_FIM_flood-risk-mapping',
    'NASA_SWOT-hydrology',
    'MODIS-LULC-analysis',
    'USGS_Streamflow-analysis',
    'PySWATCal'
];

/**
 * Fetch repositories from GitHub API
 * @returns {Promise<Array>} Array of repository objects
 */
async function fetchRepositories() {
    try {
        const response = await fetch(
            `https://api.github.com/users/${GITHUB_USERNAME}/repos?sort=updated&per_page=100`
        );

        if (!response.ok) {
            throw new Error(`GitHub API error: ${response.status}`);
        }

        const repos = await response.json();
        return repos.filter(repo => FEATURED_REPOS.includes(repo.name));
    } catch (error) {
        console.error('Error fetching repositories:', error);
        return [];
    }
}

/**
 * Create a project card element
 * @param {Object} repo - Repository data from GitHub API
 * @returns {HTMLElement} Project card element
 */
function createProjectCard(repo) {
    const card = document.createElement('div');
    card.className = 'project-card';

    const title = document.createElement('h3');
    title.textContent = repo.name.replace(/_/g, ' ').replace(/-/g, ' ');

    const description = document.createElement('p');
    description.textContent = repo.description || 'No description available';

    const link = document.createElement('a');
    link.href = repo.html_url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = 'View on GitHub →';

    const meta = document.createElement('div');
    meta.className = 'project-meta';
    meta.innerHTML = `
        <span title="Stars">⭐ ${repo.stargazers_count}</span>
        <span title="Forks">🍴 ${repo.forks_count}</span>
        <span title="Language">💻 ${repo.language || 'N/A'}</span>
    `;
    meta.style.cssText = 'margin-top: 0.5rem; color: #8b949e; font-size: 0.85rem; display: flex; gap: 1rem;';

    card.appendChild(title);
    card.appendChild(description);
    card.appendChild(meta);
    card.appendChild(link);

    return card;
}

/**
 * Render projects to the grid
 * @param {Array} repos - Array of repository objects
 */
function renderProjects(repos) {
    const grid = document.getElementById('projectGrid');

    if (!grid) return;

    grid.innerHTML = '';

    if (repos.length === 0) {
        grid.innerHTML = '<p style="color: #8b949e;">Unable to load projects. Please visit <a href="https://github.com/ductran27" style="color: #0366d6;">GitHub</a> directly.</p>';
        return;
    }

    // Sort by featured order
    const sortedRepos = FEATURED_REPOS
        .map(name => repos.find(r => r.name === name))
        .filter(Boolean);

    sortedRepos.forEach(repo => {
        const card = createProjectCard(repo);
        grid.appendChild(card);
    });
}

/**
 * Initialize the portfolio
 */
async function init() {
    const grid = document.getElementById('projectGrid');

    if (grid) {
        grid.innerHTML = '<div class="loading"></div>';
        const repos = await fetchRepositories();
        renderProjects(repos);
    }

    // Add smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

// Run on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { fetchRepositories, createProjectCard, renderProjects };
}
