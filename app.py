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
BOOKS_PER_ROW = 6
INITIAL_ROWS = 2
ROWS_PER_LOAD = 1
CONTAINER_MAX_VISIBLE_ROWS = 3

def get_random_books(query="", current_count=0, load_more_count=0):
    """Get books for random section with pagination"""
    if query:
        query = query.strip().lower()
        mask_title = df["title_lower"].str.contains(query, na=False)
        mask_authors = df["authors_lower"].apply(lambda lst: any(query in a for a in lst))
        mask_genres = df["genres_lower"].apply(lambda lst: any(query in g for g in lst))
        filtered = df[mask_title | mask_authors | mask_genres]
        
        if len(filtered) == 0:
            return filtered
        # For searched results, return paginated results
        total_needed = (INITIAL_ROWS + load_more_count) * BOOKS_PER_ROW
        return filtered.head(total_needed)
    else:
        # No query - return true random sample
        total_needed = (INITIAL_ROWS + load_more_count) * BOOKS_PER_ROW
        if len(df) <= total_needed:
            return df
        return df.sample(n=min(total_needed, len(df)))

def get_popular_books(current_count=0, load_more_count=0):
    """Get books for popular section with pagination"""
    total_needed = (INITIAL_ROWS + load_more_count) * BOOKS_PER_ROW
    return df.head(total_needed)

def create_book_card(img_url, title, authors, genres):
    """Create HTML card for a book"""
    genres_text = ", ".join(genres[:2])  # Show max 2 genres for compact layout
    authors_text = ", ".join(authors)
    
    return f"""
    <div class="book-card">
        <img src="{img_url}" alt="{title}" onerror="this.src='https://via.placeholder.com/150x220/667eea/white?text=No+Image'">
        <div class="book-info">
            <div class="book-title" title="{title}">{title}</div>
            <div class="book-authors" title="{authors_text}">by {authors_text}</div>
            <div class="book-genres" title="{genres_text}">{genres_text}</div>
        </div>
    </div>
    """

def create_books_grid(books_df, section_type, load_more_count=0):
    """Create grid layout with books"""
    if books_df.empty:
        return f"""
        <div class="books-container" id="{section_type}-container">
            <div class="empty-message">No books found. Try a different search.</div>
            <div class="load-more-bottom">
                <div class="load-more-placeholder"></div>
            </div>
        </div>
        """
    
    total_rows = INITIAL_ROWS + load_more_count
    books_per_load = ROWS_PER_LOAD * BOOKS_PER_ROW
    
    # Create rows of books
    rows_html = ""
    for row_idx in range(total_rows):
        start_idx = row_idx * BOOKS_PER_ROW
        end_idx = start_idx + BOOKS_PER_ROW
        row_books = books_df.iloc[start_idx:end_idx]
        
        if row_books.empty:
            break
            
        row_html = ""
        for _, book in row_books.iterrows():
            card = create_book_card(
                book["image_url"],
                book["title"],
                book["authors"],
                book["genres"]
            )
            row_html += card
        
        rows_html += f'<div class="book-row">{row_html}</div>'
    
    # Show remaining count if there are more books available
    remaining_text = ""
    total_available = len(books_df)
    total_shown = total_rows * BOOKS_PER_ROW
    if total_shown < total_available:
        remaining = total_available - total_shown
        remaining_text = f'<div class="remaining-count">+{remaining} more books available</div>'
    
    return f"""
    <div class="books-container" id="{section_type}-container">
        <div class="books-grid">
            {rows_html}
        </div>
        {remaining_text}
        <div class="load-more-bottom">
            <div class="load-more-placeholder"></div>
        </div>
    </div>
    """

# Initial load - show random books and popular books
def initial_load(query=""):
    # Random books (affected by search)
    random_books = get_random_books(query=query, current_count=0, load_more_count=0)
    random_html = create_books_grid(random_books, "random", 0)
    
    # Popular books (UNAFFECTED by search)
    popular_books = get_popular_books(current_count=0, load_more_count=0)
    popular_html = create_books_grid(popular_books, "popular", 0)
    
    # Check if more books are available
    random_has_more = len(random_books) > INITIAL_ROWS * BOOKS_PER_ROW
    popular_has_more = len(popular_books) > INITIAL_ROWS * BOOKS_PER_ROW
    
    if query:
        total_random = len(df[df["title_lower"].str.contains(query, na=False) | 
                             df["authors_lower"].apply(lambda lst: any(query in a for a in lst)) |
                             df["genres_lower"].apply(lambda lst: any(query in g for g in lst))])
        results_text = f"🎲 Found {total_random} books for '{query}'"
    else:
        results_text = "🎲 Discover Random Books"
    
    return (random_html, popular_html, 0, 0, 
            gr.update(visible=random_has_more), 
            gr.update(visible=popular_has_more), 
            results_text)

# Load more functionality for random books
def load_more_random(query, load_more_count, current_random_html):
    load_more_count += 1
    random_books = get_random_books(query=query, current_count=0, load_more_count=load_more_count)
    random_html = create_books_grid(random_books, "random", load_more_count)
    
    # Check if more books are available
    total_shown = (INITIAL_ROWS + load_more_count) * BOOKS_PER_ROW
    random_has_more = len(random_books) > total_shown
    
    return random_html, load_more_count, gr.update(visible=random_has_more)

# Load more functionality for popular books
def load_more_popular(load_more_count, current_popular_html):
    load_more_count += 1
    popular_books = get_popular_books(current_count=0, load_more_count=load_more_count)
    popular_html = create_books_grid(popular_books, "popular", load_more_count)
    
    # Check if more books are available
    total_shown = (INITIAL_ROWS + load_more_count) * BOOKS_PER_ROW
    popular_has_more = len(popular_books) > total_shown
    
    return popular_html, load_more_count, gr.update(visible=popular_has_more)

# Refresh random books - reset to initial state
def refresh_random(query):
    random_books = get_random_books(query=query, current_count=0, load_more_count=0)
    random_html = create_books_grid(random_books, "random", 0)
    
    # Check if more books are available
    random_has_more = len(random_books) > INITIAL_ROWS * BOOKS_PER_ROW
    
    if query:
        total_random = len(df[df["title_lower"].str.contains(query, na=False) | 
                             df["authors_lower"].apply(lambda lst: any(query in a for a in lst)) |
                             df["genres_lower"].apply(lambda lst: any(query in g for g in lst))])
        results_text = f"🎲 Found {total_random} books for '{query}'"
    else:
        results_text = "🎲 Discover Random Books"
    
    return random_html, 0, gr.update(visible=random_has_more), results_text

# Clear search
def clear_search():
    return "", *initial_load("")

# Build UI with the new container approach
with gr.Blocks(css="""
    .gallery-container {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
        background: white;
    }
    .books-container {
        height: 480px; /* Fixed height for 3 rows */
        overflow-y: auto;
        border: 1px solid #f0f0f0;
        border-radius: 8px;
        padding: 15px;
        background: #fafafa;
    }
    .books-grid {
        display: flex;
        flex-direction: column;
        gap: 15px;
    }
    .book-row {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 15px;
    }
    .book-card {
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        height: 140px; /* Compact height */
    }
    .book-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    .book-card img {
        width: 100%;
        height: 90px;
        object-fit: cover;
        border-bottom: 1px solid #f0f0f0;
    }
    .book-info {
        padding: 8px;
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .book-title {
        font-weight: bold;
        font-size: 11px;
        line-height: 1.2;
        margin-bottom: 3px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        color: #2c3e50;
    }
    .book-authors {
        font-size: 9px;
        color: #666;
        margin-bottom: 2px;
        display: -webkit-box;
        -webkit-line-clamp: 1;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .book-genres {
        font-size: 8px;
        color: #888;
        font-style: italic;
        display: -webkit-box;
        -webkit-line-clamp: 1;
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
    .load-more-bottom {
        display: flex;
        justify-content: center;
        margin-top: 20px;
        padding-top: 15px;
        border-top: 1px solid #e0e0e0;
    }
    .load-more-placeholder {
        height: 20px; /* Space for the button */
    }
    .empty-message {
        text-align: center;
        padding: 40px;
        color: #666;
        font-style: italic;
    }
    .remaining-count {
        text-align: center;
        font-size: 12px;
        color: #888;
        margin: 10px 0;
        font-style: italic;
    }
    /* Custom scrollbar */
    .books-container::-webkit-scrollbar {
        width: 6px;
    }
    .books-container::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 3px;
    }
    .books-container::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 3px;
    }
    .books-container::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
    }
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
            
            with gr.Row():
                load_more_random_btn = gr.Button(
                    "📚 Load More Random Books", 
                    visible=False, 
                    variant="primary"
                )
                random_load_more_state = gr.State(0)
        
        # Popular Books Section
        with gr.Column(elem_classes="gallery-container"):
            with gr.Row(elem_classes="section-header"):
                gr.Markdown("📚 Popular Books", elem_classes="section-title")
            
            popular_html = gr.HTML()
            
            with gr.Row():
                load_more_popular_btn = gr.Button(
                    "📚 Load More Popular Books", 
                    visible=False, 
                    variant="primary"
                )
                popular_load_more_state = gr.State(0)
    
    # Event handlers
    search_box.submit(
        initial_load, 
        inputs=[search_box], 
        outputs=[random_html, popular_html, random_load_more_state, popular_load_more_state, 
                load_more_random_btn, load_more_popular_btn, random_results_info]
    )
    
    load_more_random_btn.click(
        load_more_random,
        inputs=[search_box, random_load_more_state, random_html],
        outputs=[random_html, random_load_more_state, load_more_random_btn]
    )
    
    load_more_popular_btn.click(
        load_more_popular,
        inputs=[popular_load_more_state, popular_html],
        outputs=[popular_html, popular_load_more_state, load_more_popular_btn]
    )
    
    clear_btn.click(
        clear_search,
        outputs=[search_box, random_html, popular_html, random_load_more_state, popular_load_more_state, 
                load_more_random_btn, load_more_popular_btn, random_results_info]
    )
    
    refresh_btn.click(
        refresh_random,
        inputs=[search_box],
        outputs=[random_html, random_load_more_state, load_more_random_btn, random_results_info]
    )
    
    # Load default books when app starts
    demo.load(
        initial_load,
        inputs=[search_box],
        outputs=[random_html, popular_html, random_load_more_state, popular_load_more_state, 
                load_more_random_btn, load_more_popular_btn, random_results_info]
    )

if __name__ == "__main__":
    demo.launch()