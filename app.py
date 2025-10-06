import ast
import pandas as pd
import gradio as gr
from gradio_modal import Modal
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

# Add ID column if not exists
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

# Simple settings
BOOKS_PER_LOAD = 12  # 2 rows of 6 books

def search_books(query, page=0):
    """Search books with pagination"""
    query = query.strip().lower()
    
    if query:
        mask_title = df["title_lower"].str.contains(query, na=False)
        mask_authors = df["authors_lower"].apply(lambda lst: any(query in a for a in lst))
        mask_genres = df["genres_lower"].apply(lambda lst: any(query in g for g in lst))
        filtered = df[mask_title | mask_authors | mask_genres]
    else:
        # For random books when no query, shuffle for variety
        filtered = df.copy().sample(frac=1).reset_index(drop=True)
    
    # Pagination
    start_idx = page * BOOKS_PER_LOAD
    end_idx = start_idx + BOOKS_PER_LOAD
    page_books = filtered.iloc[start_idx:end_idx]
    
    has_more = len(filtered) > end_idx
    return page_books, has_more

def get_popular_books(page=0):
    """Get popular books with pagination"""
    # For demo, just use the dataframe as-is. You can replace with actual popularity logic
    start_idx = page * BOOKS_PER_LOAD
    end_idx = start_idx + BOOKS_PER_LOAD
    page_books = df.iloc[start_idx:end_idx]
    
    has_more = len(df) > end_idx
    return page_books, has_more

def create_book_card(img_url, title, authors, genres, book_id):
    """Create a book card"""
    return f"""
    <div class="book-card" data-book-id="{book_id}">
        <img src="{img_url}" onerror="this.src='https://via.placeholder.com/150x220/667eea/white?text=No+Image'">
        <div class="book-info">
            <div class="title">{title}</div>
            <div class="authors">by {', '.join(authors)}</div>
            <div class="genres">{', '.join(genres[:2])}</div>
        </div>
    </div>
    """

def create_books_display(books_df):
    """Create the books display grid"""
    if books_df.empty:
        return "<div class='no-books'>No books found</div>"
    
    books_html = "".join([
        create_book_card(row["image_url"], row["title"], row["authors"], row["genres"], row["id"])
        for _, row in books_df.iterrows()
    ])
    
    return f'<div class="books-grid">{books_html}</div>'

def get_book_details(book_id):
    """Get detailed information for a specific book"""
    if book_id is None:
        return "Select a book to see details"
    
    book = df[df["id"] == book_id].iloc[0]
    
    title = book["title"]
    authors = ", ".join(book["authors"])
    genres = ", ".join(book["genres"])
    description = book.get("description", "No description available.")
    image_url = book["image_url"]
    
    # Additional details
    year = book.get("published_year", "Unknown")
    rating = book.get("average_rating", "Not rated")
    pages = book.get("num_pages", "Unknown")
    
    details_html = f"""
    <div style="display: grid; grid-template-columns: 200px 1fr; gap: 20px; align-items: start;">
        <div>
            <img src="{image_url}" style="width: 100%; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);" 
                 onerror="this.src='https://via.placeholder.com/200x300/667eea/white?text=No+Image'">
        </div>
        <div>
            <h2 style="margin: 0 0 10px 0; color: #2c3e50;">{title}</h2>
            <p style="margin: 5px 0; color: #666;"><strong>Author(s):</strong> {authors}</p>
            <p style="margin: 5px 0; color: #666;"><strong>Genres:</strong> {genres}</p>
            <p style="margin: 5px 0; color: #666;"><strong>Published:</strong> {year}</p>
            <p style="margin: 5px 0; color: #666;"><strong>Rating:</strong> {rating}</p>
            <p style="margin: 5px 0; color: #666;"><strong>Pages:</strong> {pages}</p>
            <div style="margin-top: 20px;">
                <h4 style="margin: 0 0 10px 0; color: #2c3e50;">Description</h4>
                <p style="line-height: 1.6; color: #555; max-height: 300px; overflow-y: auto;">{description}</p>
            </div>
        </div>
    </div>
    """
    return details_html

def show_book_details(book_id):
    """Show book details in modal"""
    details_html = get_book_details(book_id)
    return gr.update(visible=True), details_html

# State management for loaded books
random_loaded_books = gr.State(pd.DataFrame())
popular_loaded_books = gr.State(pd.DataFrame())

def initial_state(query=""):
    """Initialize or reset the application state"""
    # Random books (searchable)
    random_books, random_has_more = search_books(query, 0)
    random_display = create_books_display(random_books)
    
    # Popular books (fixed)
    popular_books, popular_has_more = get_popular_books(0)
    popular_display = create_books_display(popular_books)
    
    # Results text
    if query:
        results_text = f"🎲 Showing results for '{query}'"
    else:
        results_text = "🎲 Discover Random Books"
    
    return (
        random_display, popular_display, 
        1, 1,  # page states (next page to load)
        gr.update(visible=random_has_more), 
        gr.update(visible=popular_has_more),
        results_text,
        random_books,  # Store loaded books in state
        popular_books
    )

def load_more_random(query, current_page, current_books_df):
    """Load more books for random/search section"""
    new_books, has_more = search_books(query, current_page)
    
    if not new_books.empty:
        # Combine with existing books
        combined_books = pd.concat([current_books_df, new_books], ignore_index=True)
        combined_display = create_books_display(combined_books)
        return combined_display, current_page + 1, gr.update(visible=has_more), combined_books
    else:
        return create_books_display(current_books_df), current_page, gr.update(visible=False), current_books_df

def load_more_popular(current_page, current_books_df):
    """Load more books for popular section"""
    new_books, has_more = get_popular_books(current_page)
    
    if not new_books.empty:
        # Combine with existing books
        combined_books = pd.concat([current_books_df, new_books], ignore_index=True)
        combined_display = create_books_display(combined_books)
        return combined_display, current_page + 1, gr.update(visible=has_more), combined_books
    else:
        return create_books_display(current_books_df), current_page, gr.update(visible=False), current_books_df

def refresh_random(query):
    """Refresh random books section"""
    random_books, random_has_more = search_books(query, 0)
    random_display = create_books_display(random_books)
    return random_display, 1, gr.update(visible=random_has_more), random_books

def clear_search():
    """Clear search and reset to initial state"""
    return "", *initial_state("")

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
        text-align: center;
        height: 280px;
        display: flex;
        flex-direction: column;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .book-card:hover {
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
    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
    }
    .section-title {
        font-size: 18px;
        font-weight: bold;
        color: #2c3e50;
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
    
    # Book Details Modal
    with Modal("📖 Book Details", visible=False) as modal:
        book_details_html = gr.HTML()
        close_btn = gr.Button("Close", variant="secondary")
    
    # Hidden component to track book clicks
    book_click_trigger = gr.Textbox(visible=False, label="Book ID")
    
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
            random_page = gr.State(1)  # Start from page 1 since page 0 is loaded initially
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

    # JavaScript for handling book clicks
    demo.load(
        None,
        None,
        None,
        js="""
        function setupBookClicks() {
            // Add click listeners to all book cards
            document.addEventListener('click', function(e) {
                const bookCard = e.target.closest('.book-card');
                if (bookCard) {
                    const bookId = bookCard.getAttribute('data-book-id');
                    if (bookId) {
                        // Find the hidden textbox and update it
                        const hiddenInput = document.querySelector('input[type="text"][style*="display: none"]');
                        if (hiddenInput) {
                            hiddenInput.value = bookId;
                            hiddenInput.dispatchEvent(new Event('input', { bubbles: true }));
                        }
                    }
                }
            });
        }
        
        // Set up book clicks when page loads
        setTimeout(setupBookClicks, 1000);
        """
    )

    # Event handlers
    search_box.submit(
        initial_state,
        [search_box],
        [random_display, popular_display, random_page, popular_page, load_random_btn, load_popular_btn, random_title, random_loaded_books, popular_loaded_books]
    )
    
    load_random_btn.click(
        load_more_random,
        [search_box, random_page, random_loaded_books],
        [random_display, random_page, load_random_btn, random_loaded_books]
    )
    
    load_popular_btn.click(
        load_more_popular,
        [popular_page, popular_loaded_books],
        [popular_display, popular_page, load_popular_btn, popular_loaded_books]
    )
    
    refresh_btn.click(
        refresh_random,
        [search_box],
        [random_display, random_page, load_random_btn, random_loaded_books]
    )
    
    clear_btn.click(
        clear_search,
        [],
        [search_box, random_display, popular_display, random_page, popular_page, load_random_btn, load_popular_btn, random_title, random_loaded_books, popular_loaded_books]
    )
    
    # Book click handler
    book_click_trigger.input(
        show_book_details,
        [book_click_trigger],
        [modal, book_details_html]
    )
    
    # Close modal handler
    close_btn.click(
        lambda: gr.update(visible=False),
        [],
        [modal]
    )

    demo.load(
        initial_state,
        [search_box],
        [random_display, popular_display, random_page, popular_page, load_random_btn, load_popular_btn, random_title, random_loaded_books, popular_loaded_books]
    )

demo.launch()