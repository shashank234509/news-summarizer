document.addEventListener('DOMContentLoaded', () => {
    fetchArchive();

    const form = document.getElementById('generate-form');
    const input = document.getElementById('goal-input');
    const btn = document.getElementById('generate-btn');
    const btnText = btn.querySelector('.btn-text');
    const spinner = btn.querySelector('.spinner');
    const statusBox = document.getElementById('status-container');
    const resultsView = document.getElementById('results-view');
    const iframe = document.getElementById('newsletter-preview');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const goal = input.value.trim();
        if(!goal) return;

        // UI Loading State
        btn.disabled = true;
        btnText.textContent = 'Working...';
        spinner.classList.remove('hidden');
        statusBox.classList.remove('hidden');
        resultsView.classList.add('hidden');

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ goal })
            });

            if(!response.ok) {
                throw new Error('Generation failed');
            }

            const data = await response.json();
            
            // Show Results
            resultsView.classList.remove('hidden');
            iframe.srcdoc = data.html;

            // Refresh Archive
            setTimeout(fetchArchive, 1000);

        } catch (error) {
            alert('An error occurred during generation: ' + error.message);
        } finally {
            // Reset UI State
            btn.disabled = false;
            btnText.textContent = 'Generate Newsletter';
            spinner.classList.add('hidden');
            statusBox.classList.add('hidden');
        }
    });
});

async function fetchArchive() {
    try {
        const res = await fetch('/api/archive');
        if(!res.ok) return;
        const data = await res.json();
        
        const grid = document.getElementById('archive-grid');
        grid.innerHTML = ''; // clear

        if(data.length === 0) {
            grid.innerHTML = '<p class="subtitle">No archived articles yet.</p>';
            return;
        }

        // Sort latest first if possible, assuming data is array
        // We'll reverse to show newest added
        data.slice().reverse().forEach(item => {
            const card = document.createElement('div');
            card.className = 'archive-card';
            
            const date = item.covered_date || 'Unknown Date';
            const title = item.title || 'Untitled';
            const summary = item.summary || 'No summary available.';
            const url = item.url || '#';

            card.innerHTML = `
                <div class="archive-date">${date}</div>
                <h3 class="archive-title"><a href="${url}" target="_blank">${title}</a></h3>
                <p class="archive-summary">${summary}</p>
            `;
            grid.appendChild(card);
        });
    } catch (e) {
        console.error('Failed to fetch archive', e);
    }
}
