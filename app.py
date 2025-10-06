import ast
import pandas as pd
import gradio as gr
import random

# Load dataset
df = pd.read_csv("data_mini_books.csv")

# Convert string lists to Python lists
df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# Create searchable columns
df["title_lower"] = df["title"].str.lower()
df["authors_lower"] = df["authors"].apply(lambda lst: [a.lower() for a in lst])
df["genres_lower"] = df["genres"].apply(lambda lst: [g.lower() for g in lst])

# Add ID column
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

# Simple settings
BOOKS_PER_LOAD = 12

def search_books(query, page=0):
    """Search books with pagination"""
    query = query.strip().lower()
    
    if query:
        mask_title = df["title_lower"].str.contains(query, na=False)
        mask_authors = df["authors_lower"].apply(lambda lst: any(query in a for a in lst))
        mask_genres = df["genres_lower"].apply(lambda lst: any(query in g for g in lst))
        filtered = df[mask_title | mask_authors | mask_genres]
    else:
        filtered = df.copy().sample(frac=1).reset_index(drop=True)
    
    start_idx = page * BOOKS_PER_LOAD
    end_idx = start_idx + BOOKS_PER_LOAD
    page_books = filtered.iloc[start_idx:end_idx]
    
    has_more = len(filtered) > end_idx
    return page_books, has_more

def get_popular_books(page=0):
    """Get popular books with pagination"""
    start_idx = page * BOOKS_PER_LOAD
    end_idx = start_idx + BOOKS_PER_LOAD
    page_books = df.iloc[start_idx:end_idx]
    
    has_more = len(df) > end_idx
    return page_books, has_more

def create_book_card(book_row, is_expanded=False):
    """Create a book card that can be expanded"""
    book_id = book_row["id"]
    title = book_row["title"]
    authors = book_row["authors"]
    genres = book_row["genres"]
    image_url = book_row["image_url"]
    description = book_row.get("description", "No description available.")
    
    # Additional details
    year = book_row.get("published_year", "Unknown")
    rating = book_row.get("average_rating", "Not rated")
    pages = book_row.get("num_pages", "Unknown")
    
    if is_expanded:
        # Expanded view - wide card with full details
        return f"""
        <div class="book-card expanded" data-book-id="{book_id}">
            <div class="expanded-content">
                <div class="expanded-left">
                    <img src="{image_url}" onerror="this.src='https://via.placeholder.com/200x300/667eea/white?text=No+Image'">
                    <button class="collapse-btn" onclick="collapseBook('{book_id}')">✕ Collapse</button>
                </div>
                <div class="expanded-right">
                    <h3>{title}</h3>
                    <p class="authors">by {', '.join(authors)}</p>
                    <div class="book-meta">
                        <span><strong>Genres:</strong> {', '.join(genres)}</span>
                        <span><strong>Published:</strong> {year}</span>
                        <span><strong>Rating:</strong> {rating}</span>
                        <span><strong>Pages:</strong> {pages}</span>
                    </div>
                    <div class="description">
                        <h4>Description</h4>
                        <p>{description}</p>
                    </div>
                </div>
            </div>
        </div>
        """
    else:
        # Collapsed view - small card
        return f"""
        <div class="book-card collapsed" data-book-id="{book_id}">
            <img src="{image_url}" onerror="this.src='https://via.placeholder.com/150x220/667eea/white?text=No+Image'">
            <div class="book-info">
                <div class="title">{title}</div>
                <div class="authors">by {', '.join(authors)}</div>
                <div class="genres">{', '.join(genres[:2])}</div>
                <button class="expand-btn" onclick="expandBook('{book_id}')">View Details</button>
            </div>
        </div>
        """

def create_books_display(books_df, expanded_book_id=None):
    """Create the books display grid"""
    if books_df.empty:
        return "<div class='no-books'>No books found</div>"
    
    books_html = "".join([
        create_book_card(row, is_expanded=(str(row["id"]) == expanded_book_id))
        for _, row in books_df.iterrows()
    ])
    
    return f'<div class="books-grid">{books_html}</div>'

# State management
random_loaded_books = gr.State(pd.DataFrame())
popular_loaded_books = gr.State(pd.DataFrame())
expanded_book = gr.State(None)  # Track which book is expanded

def initial_state(query=""):
    """Initialize or reset the application state"""
    random_books, random_has_more = search_books(query, 0)
    popular_books, popular_has_more = get_popular_books(0)
    
    if query:
        results_text = f"🎲 Showing results for '{query}'"
    else:
        results_text = "🎲 Discover Random Books"
    
    return (
        random_books, popular_books,
        1, 1,
        gr.update(visible=random_has_more), 
        gr.update(visible=popular_has_more),
        results_text,
        random_books,
        popular_books,
        None  # expanded_book
    )

def load_more_random(query, current_page, current_books_df, expanded_book_id):
    new_books, has_more = search_books(query, current_page)
    
    if not new_books.empty:
        combined_books = pd.concat([current_books_df, new_books], ignore_index=True)
        random_display = create_books_display(combined_books, expanded_book_id)
        return random_display, current_page + 1, gr.update(visible=has_more), combined_books
    else:
        random_display = create_books_display(current_books_df, expanded_book_id)
        return random_display, current_page, gr.update(visible=False), current_books_df

def load_more_popular(current_page, current_books_df, expanded_book_id):
    new_books, has_more = get_popular_books(current_page)
    
    if not new_books.empty:
        combined_books = pd.concat([current_books_df, new_books], ignore_index=True)
        popular_display = create_books_display(combined_books, expanded_book_id)
        return popular_display, current_page + 1, gr.update(visible=has_more), combined_books
    else:
        popular_display = create_books_display(current_books_df, expanded_book_id)
        return popular_display, current_page, gr.update(visible=False), current_books_df

def refresh_random(query, expanded_book_id):
    random_books, random_has_more = search_books(query, 0)
    random_display = create_books_display(random_books, expanded_book_id)
    return random_display, 1, gr.update(visible=random_has_more), random_books

def clear_search():
    return "", *initial_state("")

def expand_book_action(book_id, current_random_books, current_popular_books):
    """Expand a book card"""
    random_display = create_books_display(current_random_books, book_id)
    popular_display = create_books_display(current_popular_books, book_id)
    return random_display, popular_display, book_id

def collapse_book_action(current_random_books, current_popular_books):
    """Collapse all book cards"""
    random_display = create_books_display(current_random_books, None)
    popular_display = create_books_display(current_popular_books, None)
    return random_display, popular_display, None

# Build the interface
with gr.Blocks(css="""
    .container {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .books-container {
        max-height: 500px;
        overflow-y: auto;
        padding: 15px;
        background: #fafafa;
        border-radius: 8px;
        border: 1px solid #f0f0f0;
        margin-bottom: 15px;
    }
    .books-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
        gap: 15px;
    }
    .book-card {
        background: white;
        border-radius: 8px;
        padding: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .book-card.collapsed {
        text-align: center;
        height: 280px;
        display: flex;
        flex-direction: column;
        cursor: pointer;
    }
    .book-card.expanded {
        grid-column: 1 / -1;
        margin: 10px 0;
        padding: 20px;
    }
    .book-card.collapsed:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    .book-card img {
        width: 100%;
        height: 160px;
        object-fit: cover;
        border-radius: 4px;
        margin-bottom: 8px;
    }
    .book-info {
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .title {
        font-weight: bold;
        font-size: 12px;
        line-height: 1.3;
        margin-bottom: 4px;
        color: #2c3e50;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .authors {
        font-size: 10px;
        color: #666;
        margin-bottom: 3px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .genres {
        font-size: 9px;
        color: #888;
        font-style: italic;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .expand-btn, .collapse-btn {
        background: #667eea;
        color: white;
        border: none;
        padding: 6px 12px;
        border-radius: 4px;
        font-size: 10px;
        cursor: pointer;
        margin-top: 8px;
        width: 100%;
    }
    .expand-btn:hover, .collapse-btn:hover {
        background: #5a67d8;
    }
    .expanded-content {
        display: grid;
        grid-template-columns: 200px 1fr;
        gap: 20px;
        align-items: start;
    }
    .expanded-left {
        text-align: center;
    }
    .expanded-left img {
        width: 100%;
        max-width: 200px;
        height: auto;
        margin-bottom: 15px;
    }
    .expanded-right h3 {
        margin: 0 0 10px 0;
        color: #2c3e50;
        font-size: 1.5em;
    }
    .expanded-right .authors {
        font-size: 1.1em;
        color: #666;
        margin-bottom: 15px;
    }
    .book-meta {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-bottom: 20px;
        padding: 15px;
        background: #f8f9fa;
        border-radius: 8px;
    }
    .book-meta span {
        font-size: 0.9em;
    }
    .description h4 {
        margin: 0 0 10px 0;
        color: #2c3e50;
    }
    .description p {
        line-height: 1.6;
        color: #555;
        max-height: 200px;
        overflow-y: auto;
    }
    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
    }
    .load-more-btn {
        display: flex;
        justify-content: center;
        margin-top: 10px;
    }
    .no-books {
        text-align: center;
        padding: 40px;
        color: #666;
        font-style: italic;
    }
    .books-container::-webkit-scrollbar {
        width: 8px;
    }
    .books-container::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    .books-container::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 4px;
    }
    .books-container::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
    }
    .search-row {
        margin-bottom: 20px;
    }
""") as demo:

    gr.Markdown("# 📚 Book Explorer")
    
    # Hidden components for book interactions
    book_click_trigger = gr.Textbox(visible=False, label="Book ID")
    collapse_trigger = gr.Button("Collapse All", visible=False)
    
    with gr.Row(elem_classes="search-row"):
        search_box = gr.Textbox(
            label="",
            placeholder="🔍 Search books by title, author, or genre...",
            scale=4
        )
        clear_btn = gr.Button("Clear", scale=1)
    
    # Random Books Section
    with gr.Column(elem_classes="container"):
        with gr.Row(elem_classes="section-header"):
            random_title = gr.Markdown("🎲 Discover Random Books")
            refresh_btn = gr.Button("🔄 Refresh")
        
        random_display = gr.HTML(elem_classes="books-container")
        
        with gr.Row(elem_classes="load-more-btn"):
            load_random_btn = gr.Button("📚 Load More Books", visible=True)
            random_page = gr.State(1)
            random_loaded_books = gr.State(pd.DataFrame())
    
    # Popular Books Section  
    with gr.Column(elem_classes="container"):
        with gr.Row(elem_classes="section-header"):
            gr.Markdown("📚 Popular Books")
        
        popular_display = gr.HTML(elem_classes="books-container")
        
        with gr.Row(elem_classes="load-more-btn"):
            load_popular_btn = gr.Button("📚 Load More Books", visible=True)
            popular_page = gr.State(1)
            popular_loaded_books = gr.State(pd.DataFrame())
    
    # Expanded book state
    expanded_book = gr.State(None)

    # JavaScript for handling expand/collapse
    demo.load(
        None,
        None,
        None,
        js="""
        function expandBook(bookId) {
            document.getElementById('book-click-trigger').value = bookId;
            document.getElementById('book-click-trigger').dispatchEvent(new Event('input', { bubbles: true }));
        }
        
        function collapseBook(bookId) {
            document.getElementById('collapse-trigger').click();
        }
        
        // ESC key to collapse
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                document.getElementById('collapse-trigger').click();
            }
        });
        """
    )

    # Event handlers
    def handle_search(query, expanded_book_id, random_books, popular_books):
        random_books_new, popular_books_new, r_page, p_page, r_has_more, p_has_more, r_title, r_loaded, p_loaded, _ = initial_state(query)
        random_display_html = create_books_display(random_books_new, expanded_book_id)
        popular_display_html = create_books_display(popular_books_new, expanded_book_id)
        return random_display_html, popular_display_html, r_page, p_page, r_has_more, p_has_more, r_title, r_loaded, p_loaded

    search_box.submit(
        handle_search,
        [search_box, expanded_book, random_loaded_books, popular_loaded_books],
        [random_display, popular_display, random_page, popular_page, load_random_btn, load_popular_btn, random_title, random_loaded_books, popular_loaded_books]
    )
    
    # Expand book
    book_click_trigger.input(
        expand_book_action,
        [book_click_trigger, random_loaded_books, popular_loaded_books],
        [random_display, popular_display, expanded_book]
    )
    
    # Collapse book
    collapse_trigger.click(
        collapse_book_action,
        [random_loaded_books, popular_loaded_books],
        [random_display, popular_display, expanded_book]
    )
    
    # Load more handlers
    load_random_btn.click(
        lambda query, page, books, expanded: load_more_random(query, page, books, expanded),
        [search_box, random_page, random_loaded_books, expanded_book],
        [random_display, random_page, load_random_btn, random_loaded_books]
    )
    
    load_popular_btn.click(
        lambda page, books, expanded: load_more_popular(page, books, expanded),
        [popular_page, popular_loaded_books, expanded_book],
        [popular_display, popular_page, load_popular_btn, popular_loaded_books]
    )
    
    refresh_btn.click(
        lambda query, expanded: refresh_random(query, expanded),
        [search_box, expanded_book],
        [random_display, random_page, load_random_btn, random_loaded_books]
    )
    
    clear_btn.click(
        lambda: ("",) + initial_state("")[:2] + (None,),
        [],
        [search_box, random_display, popular_display, random_page, popular_page, load_random_btn, load_popular_btn, random_title, random_loaded_books, popular_loaded_books, expanded_book]
    )

    # Initial load
    demo.load(
        lambda: (create_books_display(pd.DataFrame()), create_books_display(pd.DataFrame())) + initial_state("")[2:],
        [],
        [random_display, popular_display, random_page, popular_page, load_random_btn, load_popular_btn, random_title, random_loaded_books, popular_loaded_books, expanded_book]
    )

demo.launch()