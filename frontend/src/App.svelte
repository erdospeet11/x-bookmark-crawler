<script>
    import { onMount } from "svelte";

    let bookmarks = [];
    let filteredBookmarks = [];
    let loading = true;
    let error = null;

    let searchQuery = "";
    let filterType = "all";

    let currentPage = 1;
    const PAGE_SIZE = 50;

    $: totalPages = Math.ceil(filteredBookmarks.length / PAGE_SIZE);
    $: visibleBookmarks = filteredBookmarks.slice(
        (currentPage - 1) * PAGE_SIZE,
        currentPage * PAGE_SIZE,
    );

    $: {
        if (searchQuery || filterType) {
            currentPage = 1;
        }
    }

    onMount(async () => {
        try {
            const res = await fetch("/bookmarks_clean.json");
            if (!res.ok)
                throw new Error(
                    "Failed to load bookmarks. Did you run the scraper?",
                );
            bookmarks = await res.json();
            applyFilters();
        } catch (e) {
            error = e.message;
        } finally {
            loading = false;
        }
    });

    function changePage(newPage) {
        if (newPage >= 1 && newPage <= totalPages) {
            currentPage = newPage;
            window.scrollTo({ top: 0, behavior: "instant" });
        }
    }

    function applyFilters() {
        let result = bookmarks;

        if (filterType === "images") {
            result = result.filter((b) => b.images && b.images.length > 0);
        } else if (filterType === "videos") {
            result = result.filter((b) => b.video);
        }

        if (searchQuery) {
            const lower = searchQuery.toLowerCase();
            result = result.filter(
                (b) =>
                    b.text.toLowerCase().includes(lower) ||
                    b.user.toLowerCase().includes(lower),
            );
        }

        filteredBookmarks = result;
    }

    $: {
        searchQuery;
        filterType;
        if (bookmarks.length) applyFilters();
    }

    function formatDate(dateStr) {
        return new Date(dateStr).toLocaleDateString(undefined, {
            year: "numeric",
            month: "short",
            day: "numeric",
        });
    }
</script>

<main class="container">
    <header>
        <h1>
            X Bookmarks <span
                style="font-size: 0.6em; color: var(--text-secondary)"
                >({filteredBookmarks.length})</span
            >
        </h1>

        <div class="controls">
            <select bind:value={filterType}>
                <option value="all">All Media</option>
                <option value="images">Images Only</option>
                <option value="videos">Videos Only</option>
            </select>

            <input
                type="text"
                placeholder="Search text or user..."
                bind:value={searchQuery}
            />
        </div>
    </header>

    {#if loading}
        <div class="no-bookmarks">Loading bookmarks...</div>
    {:else if error}
        <div class="no-bookmarks" style="color: #f44">
            {error}
            <br /><br />
            <small
                >Make sure `scraper/scrape.js` has been run and
                `bookmarks_clean.json` exists in `frontend/public/`.</small
            >
        </div>
    {:else if filteredBookmarks.length === 0}
        <div class="no-bookmarks">No bookmarks found matching filters.</div>
    {:else}
        <div class="grid">
            {#each visibleBookmarks as item (item.id)}
                <div class="card">
                    <div class="card-header">
                        <span class="username">@{item.user}</span>
                        <span class="date">{formatDate(item.created_at)}</span>
                    </div>

                    <div class="card-content">
                        {item.text}

                        {#if item.video}
                            <div class="media-container">
                                <!-- svelte-ignore a11y-media-has-caption -->
                                <video
                                    controls
                                    preload="metadata"
                                    poster={item.images?.[0]}
                                    playsinline
                                    referrerpolicy="no-referrer"
                                    style="min-height: 200px; background: #000;"
                                >
                                    <source src={item.video} type="video/mp4" />
                                    Your browser does not support the video tag.
                                </video>
                                <div style="text-align: right; padding: 4px;">
                                    <a
                                        href={item.video}
                                        target="_blank"
                                        style="font-size: 0.8em; color: var(--primary-color);"
                                    >
                                        &nequiv; Direct Video Link
                                    </a>
                                </div>
                            </div>
                        {:else if item.images && item.images.length > 0}
                            <div
                                class="media-container {item.images.length > 1
                                    ? `media-grid-${Math.min(item.images.length, 4)}`
                                    : ''}"
                            >
                                {#each item.images as img}
                                    <img
                                        src={img}
                                        alt="Tweet media"
                                        loading="lazy"
                                    />
                                {/each}
                            </div>
                        {/if}
                    </div>

                    <a
                        href="https://twitter.com/{item.user}/status/{item.id}"
                        target="_blank"
                        class="link-btn"
                    >
                        View on X
                    </a>
                </div>
            {/each}
        </div>

        <div class="pagination">
            <button
                class="page-btn"
                disabled={currentPage === 1}
                on:click={() => changePage(currentPage - 1)}
            >
                &larr; Prev
            </button>

            {#if totalPages > 0}
                <button
                    class="page-btn {currentPage === 1 ? 'active' : ''}"
                    on:click={() => changePage(1)}>1</button
                >
            {/if}

            {#if currentPage > 3}
                <span style="color: var(--text-secondary)">...</span>
            {/if}
            {#each [-1, 0, 1] as offset}
                {@const p = currentPage + offset}
                {#if p > 1 && p < totalPages}
                    <button
                        class="page-btn {p === currentPage ? 'active' : ''}"
                        on:click={() => changePage(p)}
                    >
                        {p}
                    </button>
                {/if}
            {/each}

            {#if currentPage < totalPages - 2}
                <span style="color: var(--text-secondary)">...</span>
            {/if}
            {#if totalPages > 1}
                <button
                    class="page-btn {currentPage === totalPages
                        ? 'active'
                        : ''}"
                    on:click={() => changePage(totalPages)}>{totalPages}</button
                >
            {/if}

            <button
                class="page-btn"
                disabled={currentPage === totalPages}
                on:click={() => changePage(currentPage + 1)}
            >
                Next &rarr;
            </button>
        </div>
    {/if}
</main>
