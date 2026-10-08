document.addEventListener("DOMContentLoaded", () => {

    const searchInput = document.getElementById("homeSearch");
    const resultsContainer = document.getElementById("homeSearchResults");

    if (!searchInput || !resultsContainer) {
        return;
    }

    let searchTimeout;

    searchInput.addEventListener("input", () => {

        clearTimeout(searchTimeout);

        const query = searchInput.value.trim();

        if (query.length < 2) {
            resultsContainer.innerHTML = "";
            resultsContainer.classList.remove("show");
            return;
        }

        searchTimeout = setTimeout(async () => {

            try {
                const response = await fetch(
                    `/api/search?q=${encodeURIComponent(query)}`
                );

                const data = await response.json();

                if (data.results.length === 0) {
                    resultsContainer.innerHTML = `
                        <div class="live-search-empty">
                            No materials found.
                        </div>
                    `;
                    resultsContainer.classList.add("show");
                    return;
                }

                resultsContainer.innerHTML = data.results.map(material => `
                    <a
                        href="/material/${material.id}"
                        class="live-search-item"
                    >
                        <div>
                            <strong>${material.title}</strong>
                            <small>
                                ${material.author} · ${material.subject}
                            </small>
                        </div>

                        <span class="live-search-status ${
                            material.available ? "available" : "unavailable"
                        }">
                            ${material.available ? "Available" : "Unavailable"}
                        </span>
                    </a>
                `).join("");

                resultsContainer.classList.add("show");

            } catch (error) {
                console.error("Live search error:", error);
            }

        }, 250);
    });

});