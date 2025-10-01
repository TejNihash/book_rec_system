import ast
import pandas as pd
import gradio as gr
import random

# Load dataset
df = pd.read_csv("data_mini_books.csv")  # columns: title, authors, genres, image_url

# Convert authors/genres from string -> Python list
df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# Lowercased helper columns
df["title_lower"] = df["title"].str.lower()
df["authors_lower"] = df["authors"].apply(lambda lst: [a.lower() for a in lst])
df["genres_lower"] = df["genres"].apply(lambda lst: [g.lower() for g in lst])

# Pagination settings
POPULAR_PAGE_SIZE = 20
RANDOM_PAGE_SIZE = 12

def get_random_books(query="", page=0, page_size=RANDOM_PAGE_SIZE):
    """Get paginated random books, filtered by query if provided"""
    if query:
        query = query.strip().lower()
        mask_title = df["title_lower"].str.contains(query, na=False)
        mask_authors = df["authors_lower"].apply(lambda lst: any(query in a for a in lst))
        mask_genres = df["genres_lower"].apply(lambda lst: any(query in g for g in lst))
        filtered = df[mask_title | mask_authors | mask_genres]
        
        if len(filtered) == 0:
            return filtered
        start = page * page_size
        end = start + page_size
        return filtered.iloc[start:end]
    else:
        if len(df) <= page_size:
            return df
        return df.sample(n=min(page_size, len(df)))

def get_popular_books(page=0, page_size=POPULAR_PAGE_SIZE):
    """Get paginated popular books (unaffected by search)"""
    filtered = df
    start = page * page_size
    end = start + page_size
    return filtered.iloc[start:end]

def create_book_card(img_url, title, authors, genres):
    """Create HTML card for a book"""
    genres_text = ", ".join(genres[:3])
    authors_text = ", ".join(authors)
    
    return f"""
    <div class="book-card">
        <img src="{img_url}" alt="{title}" onerror="this.src='https://via.placeholder.com/120x180/667eea/white?text=No+Image'">
        <div class="book-info">
            <div class="book-title" title="{title}">{title}</div>
            <div class="book-authors" title="{authors_text}">by {authors_text}</div>
            <div class="book-genres" title="{genres_text}">{genres_text}</div>
        </div>
    </div>
    """

def create_gallery_html(books_df, section_type):
    """Create horizontal scrollable gallery from dataframe"""
    if books_df.empty:
        return f"""
        <div class="gallery-wrapper" id="{section_type}-gallery">
            <div class="horizontal-scroll">
                <div class="scroll-container">
                    <div class="empty-message">No books found. Try a different search.</div>
                </div>
            </div>
            <div class="load-more-right" id="{section_type}-load-more"></div>
        </div>
        """
    
    cards_html = ""
    for _, row in books_df.iterrows():
        card = create_book_card(
            row["image_url"],
            row["title"],
            row["authors"],
            row["genres"]
        )
        cards_html += card
    
    return f"""
    <div class="gallery-wrapper" id="{section_type}-gallery">
        <div class="horizontal-scroll">
            <div class="scroll-container">
                {cards_html}
            </div>
        </div>
        <div class="load-more-right" id="{section_type}-load-more"></div>
    </div>
    """

# Initial load - show random books and popular books
def initial_load(query=""):
    # Random books (affected by search)
    random_books = get_random_books(query=query, page=0)
    random_html = create_gallery_html(random_books, "random")
    
    # Popular books (UNAFFECTED by search)
    popular_books = get_popular_books(page=0)
    popular_html = create_gallery_html(popular_books, "popular")
    
    random_has_next = len(random_books) == RANDOM_PAGE_SIZE
    popular_has_next = len(popular_books) == POPULAR_PAGE_SIZE
    
    if query:
        total_random = len(df[df["title_lower"].str.contains(query, na=False) | 
                             df["authors_lower"].apply(lambda lst: any(query in a for a in lst)) |
                             df["genres_lower"].apply(lambda lst: any(query in g for g in lst))])
        results_text = f"🎲 Found {total_random} books for '{query}' • Showing {len(random_books)}"
    else:
        results_text = "🎲 Discover Random Books"
    
    return (random_html, popular_html, 0, 0, 
            gr.update(visible=random_has_next), 
            gr.update(visible=popular_has_next), 
            results_text)

# Load more functionality for random books
def load_more_random(query, page, current_random_html):
    page += 1
    random_books = get_random_books(query=query, page=page)
    
    if random_books.empty:
        return current_random_html, page, gr.update(visible=False)
    
    # Extract just the new cards HTML
    new_cards_html = ""
    for _, row in random_books.iterrows():
        card = create_book_card(
            row["image_url"],
            row["title"],
            row["authors"],
            row["genres"]
        )
        new_cards_html += card
    
    # Insert new cards before the load-more-right div
    updated_html = current_random_html.replace(
        '<div class="load-more-right" id="random-load-more"></div>',
        new_cards_html + '<div class="load-more-right" id="random-load-more"></div>'
    )
    
    random_has_next = len(random_books) == RANDOM_PAGE_SIZE
    
    return updated_html, page, gr.update(visible=random_has_next)

# Load more functionality for popular books
def load_more_popular(page, current_popular_html):
    page += 1
    popular_books = get_popular_books(page=page)
    
    if popular_books.empty:
        return current_popular_html, page, gr.update(visible=False)
    
    # Extract just the new cards HTML
    new_cards_html = ""
    for _, row in popular_books.iterrows():
        card = create_book_card(
            row["image_url"],
            row["title"],
            row["authors"],
            row["genres"]
        )
        new_cards_html += card
    
    # Insert new cards before the load-more-right div
    updated_html = current_popular_html.replace(
        '<div class="load-more-right" id="popular-load-more"></div>',
        new_cards_html + '<div class="load-more-right" id="popular-load-more"></div>'
    )
    
    popular_has_next = len(popular_books) == POPULAR_PAGE_SIZE
    
    return updated_html, page, gr.update(visible=popular_has_next)

# Refresh random books
def refresh_random(query):
    random_books = get_random_books(query=query, page=0)
    random_html = create_gallery_html(random_books, "random")
    
    random_has_next = len(random_books) == RANDOM_PAGE_SIZE and len(random_books) < len(df)
    
    if query:
        total_random = len(df[df["title_lower"].str.contains(query, na=False) | 
                             df["authors_lower"].apply(lambda lst: any(query in a for a in lst)) |
                             df["genres_lower"].apply(lambda lst: any(query in g for g in lst))])
        results_text = f"🎲 Found {total_random} books for '{query}' • Showing {len(random_books)}"
    else:
        results_text = "🎲 Discover Random Books"
    
    return random_html, 0, gr.update(visible=random_has_next), results_text

# Clear search
def clear_search():
    return "", *initial_load("")

# Build UI with fixed scrolling and right-side load more buttons
with gr.Blocks(css="""
    .gallery-container {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
        background: white;
        position: relative;
    }
    .gallery-wrapper {
        position: relative;
        width: 100%;
    }
    .horizontal-scroll {
        width: 100%;
        overflow-x: auto;
        padding: 10px 0;
    }
    .scroll-container {
        display: flex;
        gap: 20px;
        padding: 10px 5px;
        min-height: 300px;
    }
    .book-card {
        flex: 0 0 auto;
        width: 160px;
        height: 290px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
        background: white;
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }
    .book-card:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    .book-card img {
        width: 100%;
        height: 180px;
        object-fit: cover;
        border-bottom: 1px solid #f0f0f0;
        flex-shrink: 0;
    }
    .book-info {
        padding: 12px;
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 110px;
    }
    .book-title {
        font-weight: bold;
        font-size: 13px;
        line-height: 1.3;
        margin-bottom: 6px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        color: #2c3e50;
        flex-shrink: 0;
    }
    .book-authors {
        font-size: 11px;
        color: #666;
        margin-bottom: 4px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        flex-shrink: 0;
    }
    .book-genres {
        font-size: 10px;
        color: #888;
        font-style: italic;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        flex-shrink: 0;
    }
    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        padding: 0 10px;
    }
    .section-title {
        font-size: 1.3em;
        font-weight: bold;
        color: #333;
        margin: 0;
    }
    .results-info {
        font-size: 14px;
        color: #666;
        margin: 10px 0;
        font-weight: bold;
        padding: 0 10px;
    }
    .search-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 12px;
        color: white;
        margin-bottom: 25px;
    }
    .refresh-btn {
        background: #4CAF50;
        color: white;
        border: none;
    }
    .load-more-right {
        position: absolute;
        right: 10px;
        top: 50%;
        transform: translateY(-50%);
        z-index: 10;
    }
    .load-more-container {
        display: flex;
        justify-content: center;
        margin-top: 15px;
        gap: 10px;
    }
    .empty-message {
        text-align: center;
        padding: 40px;
        color: #666;
        font-style: italic;
    }
    .horizontal-scroll::-webkit-scrollbar {
        height: 8px;
    }
    .horizontal-scroll::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    .horizontal-scroll::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 4px;
    }
    .horizontal-scroll::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
    }
    
    <script>
    // Simple scroll preservation - store position before update
    let currentScrollPositions = {};
    
    function saveScrollPosition(section) {
        const scrollContainer = document.querySelector(`#${section}-gallery .horizontal-scroll`);
        if (scrollContainer) {
            currentScrollPositions[section] = scrollContainer.scrollLeft;
        }
    }
    
    function restoreScrollPosition(section) {
        const scrollContainer = document.querySelector(`#${section}-gallery .horizontal-scroll`);
        if (scrollContainer && currentScrollPositions[section] !== undefined) {
            setTimeout(() => {
                scrollContainer.scrollLeft = currentScrollPositions[section];
            }, 50);
        }
    }
    
    // Save scroll position before any update
    document.addEventListener('DOMContentLoaded', function() {
        // Save scroll when about to load more
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('load-more-btn')) {
                const section = e.target.getAttribute('data-section');
                saveScrollPosition(section);
            }
        });
        
        // Restore scroll after Gradio updates
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    // Check if this is a gallery update
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1 && node.classList && 
                            (node.classList.contains('gallery-wrapper') || 
                             node.querySelector('.gallery-wrapper'))) {
                            const section = node.id ? node.id.replace('-gallery', '') : 
                                        node.querySelector('[id$="-gallery"]')?.id.replace('-gallery', '');
                            if (section) {
                                setTimeout(() => restoreScrollPosition(section), 100);
                            }
                        }
                    });
                }
            });
        });
        
        observer.observe(document.body, { childList: true, subtree: true });
    });
    </script>
""") as demo:
    
    with gr.Column():
        # Header
        gr.Markdown("""
        # 📚 Book Explorer
        *Discover your next favorite read*
        """, elem_classes="search-header")
        
        # Search Section
        with gr.Row():
            search_box = gr.Textbox(
                label="",
                placeholder="🔍 Search random books by title, author, or genre...",
                value="",
                scale=4
            )
            clear_btn = gr.Button("Clear Search", scale=1, variant="secondary")
        
        # Random Books Section
        with gr.Column(elem_classes="gallery-container"):
            with gr.Row(elem_classes="section-header"):
                random_results_info = gr.Markdown("🎲 Discover Random Books", elem_classes="section-title")
                refresh_btn = gr.Button("🔄 Refresh Random", elem_classes="refresh-btn", size="sm")
            
            random_html = gr.HTML()
            
            # Load More button will be positioned via CSS on the right
            with gr.Row():
                load_more_random_btn = gr.Button(
                    "➡️ Load More", 
                    visible=False, 
                    variant="primary",
                    elem_classes="load-more-btn"
                )
                random_page_state = gr.State(0)
        
        # Popular Books Section
        with gr.Column(elem_classes="gallery-container"):
            with gr.Row(elem_classes="section-header"):
                gr.Markdown("📚 Popular Books", elem_classes="section-title")
            
            popular_html = gr.HTML()
            
            # Load More button will be positioned via CSS on the right
            with gr.Row():
                load_more_popular_btn = gr.Button(
                    "➡️ Load More", 
                    visible=False, 
                    variant="primary",
                    elem_classes="load-more-btn" 
                )
                popular_page_state = gr.State(0)
    
    # Event handlers
    search_box.submit(
        initial_load, 
        inputs=[search_box], 
        outputs=[random_html, popular_html, random_page_state, popular_page_state, 
                load_more_random_btn, load_more_popular_btn, random_results_info]
    )
    
    load_more_random_btn.click(
        load_more_random,
        inputs=[search_box, random_page_state, random_html],
        outputs=[random_html, random_page_state, load_more_random_btn]
    )
    
    load_more_popular_btn.click(
        load_more_popular,
        inputs=[popular_page_state, popular_html],
        outputs=[popular_html, popular_page_state, load_more_popular_btn]
    )
    
    clear_btn.click(
        clear_search,
        outputs=[search_box, random_html, popular_html, random_page_state, popular_page_state, 
                load_more_random_btn, load_more_popular_btn, random_results_info]
    )
    
    refresh_btn.click(
        refresh_random,
        inputs=[search_box],
        outputs=[random_html, random_page_state, load_more_random_btn, random_results_info]
    )
    
    # Load default books when app starts
    demo.load(
        initial_load,
        inputs=[search_box],
        outputs=[random_html, popular_html, random_page_state, popular_page_state, 
                load_more_random_btn, load_more_popular_btn, random_results_info]
    )

if __name__ == "__main__":
    demo.launch()