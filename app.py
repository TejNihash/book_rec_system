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
RANDOM_SAMPLE_SIZE = 12  # Number of random books to show

def get_random_books(n=RANDOM_SAMPLE_SIZE, query=""):
    """Get random sample of books, filtered by query if provided"""
    if query:
        query = query.strip().lower()
        mask_title = df["title_lower"].str.contains(query, na=False)
        mask_authors = df["authors_lower"].apply(lambda lst: any(query in a for a in lst))
        mask_genres = df["genres_lower"].apply(lambda lst: any(query in g for g in lst))
        filtered = df[mask_title | mask_authors | mask_genres]
        
        if len(filtered) == 0:
            return filtered
        elif len(filtered) <= n:
            return filtered
        else:
            return filtered.sample(n=n)
    else:
        # No query - return true random sample
        if len(df) <= n:
            return df
        return df.sample(n=n)

def get_popular_books(page=0):
    """Get paginated popular books (unaffected by search)"""
    # Show popular books (first N books)
    filtered = df
    
    # Pagination
    start = page * POPULAR_PAGE_SIZE
    end = start + POPULAR_PAGE_SIZE
    page_data = filtered.iloc[start:end]

    return page_data

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

def create_gallery_html(books_df):
    """Create horizontal scrollable gallery from dataframe"""
    if books_df.empty:
        return "<div class='empty-message'>No books found. Try a different search.</div>"
    
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
    <div class="horizontal-scroll">
        <div class="scroll-container">
            {cards_html}
        </div>
    </div>
    """

# Initial load - show random books and popular books
def initial_load(query=""):
    # Random books (affected by search)
    random_books = get_random_books(query=query)
    random_html = create_gallery_html(random_books)
    
    # Popular books (UNAFFECTED by search)
    popular_books = get_popular_books(page=0)
    popular_html = create_gallery_html(popular_books)
    
    has_next = len(popular_books) == POPULAR_PAGE_SIZE
    
    if query:
        results_text = f"🎲 Found {len(random_books)} random books for '{query}'"
    else:
        results_text = "🎲 Discover Random Books"
    
    return random_html, popular_html, 0, gr.update(visible=has_next), results_text

# Load more functionality for popular books
def load_more(page, current_popular_html):
    page += 1
    popular_books = get_popular_books(page)
    new_html = create_gallery_html(popular_books)
    
    # For simplicity, we'll replace instead of append to avoid complexity
    has_next = len(popular_books) == POPULAR_PAGE_SIZE
    
    return new_html, page, gr.update(visible=has_next)

# Refresh random books (with current search if any)
def refresh_random(query):
    random_books = get_random_books(query=query)
    random_html = create_gallery_html(random_books)
    
    if query:
        results_text = f"🎲 Found {len(random_books)} random books for '{query}'"
    else:
        results_text = "🎲 Discover Random Books"
    
    return random_html, results_text

# Clear search - resets to default view
def clear_search():
    return "", *initial_load("")

# Build UI with custom HTML components for proper horizontal scrolling
with gr.Blocks(css="""
    .gallery-container {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
        background: white;
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
        min-height: 280px;
    }
    .book-card {
        flex: 0 0 auto;
        width: 160px;
        height: 280px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
        background: white;
        overflow: hidden;
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
    }
    .book-info {
        padding: 12px;
        height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .book-title {
        font-weight: bold;
        color: #777
        font-size: 12px;
        line-height: 1.2;
        margin-bottom: 4px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .book-authors {
        font-size: 11px;
        color: #666;
        margin-bottom: 4px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .book-genres {
        font-size: 10px;
        color: #888;
        font-style: italic;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
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
    .load-more-container {
        display: flex;
        justify-content: center;
        margin-top: 15px;
    }
    .empty-message {
        text-align: center;
        padding: 40px;
        color: #666;
        font-style: italic;
    }
    /* Custom scrollbar */
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
""") as demo:
    
    with gr.Column():
        # Header
        with gr.Row():
            with gr.Column():
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
        
        # Random Books Section (affected by search)
        with gr.Column(elem_classes="gallery-container"):
            with gr.Row(elem_classes="section-header"):
                random_results_info = gr.Markdown("🎲 Discover Random Books", elem_classes="section-title")
                refresh_btn = gr.Button("🔄 Refresh Random", elem_classes="refresh-btn", size="sm")
            
            random_html = gr.HTML()
        
        # Popular Books Section (UNAFFECTED by search)
        with gr.Column(elem_classes="gallery-container"):
            with gr.Row(elem_classes="section-header"):
                gr.Markdown("📚 Popular Books", elem_classes="section-title")
            
            popular_html = gr.HTML()
            
            with gr.Row(elem_classes="load-more-container"):
                load_more_button = gr.Button("📚 Load More Popular Books", visible=False, variant="primary")
                page_state = gr.State(0)
    
    # Event handlers
    search_box.submit(
        initial_load, 
        inputs=[search_box], 
        outputs=[random_html, popular_html, page_state, load_more_button, random_results_info]
    )
    
    load_more_button.click(
        load_more,
        inputs=[page_state, popular_html],
        outputs=[popular_html, page_state, load_more_button]
    )
    
    clear_btn.click(
        clear_search,
        outputs=[search_box, random_html, popular_html, page_state, load_more_button, random_results_info]
    )
    
    refresh_btn.click(
        refresh_random,
        inputs=[search_box],
        outputs=[random_html, random_results_info]
    )
    
    # Load default books when app starts
    demo.load(
        initial_load,
        inputs=[search_box],
        outputs=[random_html, popular_html, page_state, load_more_button, random_results_info]
    )

if __name__ == "__main__":
    demo.launch()