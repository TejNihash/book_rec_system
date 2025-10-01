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

# Store loaded books to maintain state
loaded_random_books = []
loaded_popular_books = []

def get_random_books(query="", page=0, reset=False):
    """Get random books, accumulating previously loaded ones"""
    global loaded_random_books
    
    if reset:
        loaded_random_books = []
    
    if query:
        query = query.strip().lower()
        mask_title = df["title_lower"].str.contains(query, na=False)
        mask_authors = df["authors_lower"].apply(lambda lst: any(query in a for a in lst))
        mask_genres = df["genres_lower"].apply(lambda lst: any(query in g for g in lst))
        filtered = df[mask_title | mask_authors | mask_genres]
        
        if len(filtered) == 0:
            return filtered
        
        # For search results, get the next chunk
        books_needed = (INITIAL_ROWS + page) * BOOKS_PER_ROW
        available_books = filtered[~filtered.index.isin([b.index for b in loaded_random_books])]
        
        if len(available_books) == 0:
            return loaded_random_books
        
        new_books = available_books.head(BOOKS_PER_ROW * ROWS_PER_LOAD)
        loaded_random_books.extend([row for _, row in new_books.iterrows()])
        
    else:
        # For random, get fresh random sample but keep previous ones
        books_needed = (INITIAL_ROWS + page) * BOOKS_PER_ROW
        if len(loaded_random_books) >= books_needed:
            return loaded_random_books[:books_needed]
        
        # Get new random books that aren't already loaded
        available_books = df[~df.index.isin([b.index for b in loaded_random_books])]
        if len(available_books) == 0:
            return loaded_random_books
        
        new_books_count = min(BOOKS_PER_ROW * ROWS_PER_LOAD, len(available_books))
        new_books = available_books.sample(n=new_books_count)
        loaded_random_books.extend([row for _, row in new_books.iterrows()])
    
    return loaded_random_books

def get_popular_books(page=0, reset=False):
    """Get popular books, accumulating previously loaded ones"""
    global loaded_popular_books
    
    if reset:
        loaded_popular_books = []
    
    books_needed = (INITIAL_ROWS + page) * BOOKS_PER_ROW
    if len(loaded_popular_books) >= books_needed:
        return loaded_popular_books[:books_needed]
    
    # Get the next chunk of popular books
    start_idx = len(loaded_popular_books)
    end_idx = start_idx + (BOOKS_PER_ROW * ROWS_PER_LOAD)
    new_books = df.iloc[start_idx:end_idx]
    
    loaded_popular_books.extend([row for _, row in new_books.iterrows()])
    return loaded_popular_books

def create_book_card(img_url, title, authors, genres):
    """Create HTML card for a book with proper sizing"""
    genres_text = ", ".join(genres[:2])
    authors_text = ", ".join(authors)
    
    return f"""
    <div class="book-card">
        <img src="{img_url}" alt="{title}" onerror="this.src='https://via.placeholder.com/180x240/667eea/white?text=No+Image'">
        <div class="book-info">
            <div class="book-title" title="{title}">{title}</div>
            <div class="book-authors" title="{authors_text}">by {authors_text}</div>
            <div class="book-genres" title="{genres_text}">{genres_text}</div>
        </div>
    </div>
    """

def create_books_container(books_list, section_type):
    """Create the books container with proper layout"""
    if not books_list:
        return f"""
        <div class="books-container" id="{section_type}-container">
            <div class="empty-message">No books found. Try a different search.</div>
        </div>
        """
    
    books_html = ""
    for book in books_list:
        card = create_book_card(
            book["image_url"],
            book["title"],
            book["authors"],
            book["genres"]
        )
        books_html += card
    
    return f"""
    <div class="books-container" id="{section_type}-container">
        <div class="books-grid">
            {books_html}
        </div>
    </div>
    """

# Initial load
def initial_load(query=""):
    # Reset and load initial books
    random_books = get_random_books(query=query, page=0, reset=True)
    random_html = create_books_container(random_books, "random")
    
    popular_books = get_popular_books(page=0, reset=True)
    popular_html = create_books_container(popular_books, "popular")
    
    # Check if more books are available
    random_has_more = len(random_books) == (INITIAL_ROWS * BOOKS_PER_ROW) and len(random_books) < len(df)
    popular_has_more = len(popular_books) == (INITIAL_ROWS * BOOKS_PER_ROW) and len(popular_books) < len(df)
    
    if query:
        total_random = len(df[df["title_lower"].str.contains(query, na=False) | 
                             df["authors_lower"].apply(lambda lst: any(query in a for a in lst)) |
                             df["genres_lower"].apply(lambda lst: any(query in g for g in lst))])
        results_text = f"🎲 Found {total_random} books for '{query}' • Showing {len(random_books)}"
    else:
        results_text = "🎲 Discover Random Books"
    
    return (random_html, popular_html, 0, 0, 
            gr.update(visible=random_has_more), 
            gr.update(visible=popular_has_more), 
            results_text)

# Load more functionality
def load_more_random(query, load_more_count, current_random_html):
    load_more_count += 1
    random_books = get_random_books(query=query, page=load_more_count, reset=False)
    random_html = create_books_container(random_books, "random")
    
    random_has_more = len(random_books) < len(df) and len(random_books) % (BOOKS_PER_ROW * ROWS_PER_LOAD) == 0
    
    return random_html, load_more_count, gr.update(visible=random_has_more)

def load_more_popular(load_more_count, current_popular_html):
    load_more_count += 1
    popular_books = get_popular_books(page=load_more_count, reset=False)
    popular_html = create_books_container(popular_books, "popular")
    
    popular_has_more = len(popular_books) < len(df) and len(popular_books) % (BOOKS_PER_ROW * ROWS_PER_LOAD) == 0
    
    return popular_html, load_more_count, gr.update(visible=popular_has_more)

# Refresh random books - resets and gets new random books
def refresh_random(query):
    random_books = get_random_books(query=query, page=0, reset=True)
    random_html = create_books_container(random_books, "random")
    
    random_has_more = len(random_books) == (INITIAL_ROWS * BOOKS_PER_ROW) and len(random_books) < len(df)
    
    if query:
        total_random = len(df[df["title_lower"].str.contains(query, na=False) | 
                             df["authors_lower"].apply(lambda lst: any(query in a for a in lst)) |
                             df["genres_lower"].apply(lambda lst: any(query in g for g in lst))])
        results_text = f"🎲 Found {total_random} books for '{query}' • Showing {len(random_books)}"
    else:
        results_text = "🎲 Discover Random Books"
    
    return random_html, 0, gr.update(visible=random_has_more), results_text

# Clear search
def clear_search():
    return "", *initial_load("")

# Build the proper UI (same CSS as before)
with gr.Blocks(css="""
    .gallery-container {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
        background: white;
    }
    .books-container {
        max-height: 500px;
        overflow-y: auto;
        padding: 15px;
        background: #fafafa;
        border-radius: 8px;
        border: 1px solid #f0f0f0;
    }
    .books-grid {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 20px;
    }
    .book-card {
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        height: 280px;
    }
    .book-card:hover {
        transform: translateY(-2px);
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
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
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
            
            with gr.Row(elem_classes="load-more-container"):
                load_more_random_btn = gr.Button("📚 Load More Random Books", visible=False, variant="primary")
                random_load_more_state = gr.State(0)
        
        # Popular Books Section
        with gr.Column(elem_classes="gallery-container"):
            with gr.Row(elem_classes="section-header"):
                gr.Markdown("📚 Popular Books", elem_classes="section-title")
            
            popular_html = gr.HTML()
            
            with gr.Row(elem_classes="load-more-container"):
                load_more_popular_btn = gr.Button("📚 Load More Popular Books", visible=False, variant="primary")
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