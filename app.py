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

def create_book_button(book_row):
    """Create a book button with proper styling"""
    title = book_row["title"]
    # Shorten long titles
    if len(title) > 30:
        title = title[:27] + "..."
    return gr.Button(title, elem_classes="book-btn"), book_row["id"]

def create_books_section(books_df, section_name):
    """Create a section with book buttons"""
    if books_df.empty:
        return gr.Column(), []
    
    buttons = []
    with gr.Column() as section:
        for _, row in books_df.iterrows():
            btn, book_id = create_book_button(row)
            buttons.append((btn, book_id))
    
    return section, buttons

def show_book_details(book_id):
    """Show book details in modal - using your working approach"""
    book = df[df["id"] == book_id].iloc[0]
    
    # Get additional details if available
    year = book.get("published_year", "Unknown")
    rating = book.get("average_rating", "Not rated")
    pages = book.get("num_pages", "Unknown")
    
    html = f"""
    <div style="max-width: 600px; max-height: 80vh; overflow-y: auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="{book['image_url']}" style="width:200px; height:auto; border-radius:8px; margin-bottom:15px;"
                 onerror="this.src='https://via.placeholder.com/200x300/667eea/white?text=No+Image'">
            <h2 style="margin: 10px 0; color: #2c3e50;">{book['title']}</h2>
            <h4 style="margin: 5px 0; color: #666;">by {', '.join(book['authors'])}</h4>
        </div>
        
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <p style="margin: 5px 0;"><strong>Genres:</strong> {', '.join(book['genres'])}</p>
            <p style="margin: 5px 0;"><strong>Published:</strong> {year}</p>
            <p style="margin: 5px 0;"><strong>Rating:</strong> {rating}</p>
            <p style="margin: 5px 0;"><strong>Pages:</strong> {pages}</p>
        </div>
        
        <div>
            <h4 style="margin: 0 0 10px 0; color: #2c3e50;">Description</h4>
            <p style="line-height: 1.6; color: #555;">{book.get('description', 'No description available.')}</p>
        </div>
    </div>
    """
    return gr.update(visible=True), html

# State management
random_loaded_books = gr.State(pd.DataFrame())
popular_loaded_books = gr.State(pd.DataFrame())

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
        popular_books
    )

def load_more_random(query, current_page, current_books_df):
    new_books, has_more = search_books(query, current_page)
    
    if not new_books.empty:
        combined_books = pd.concat([current_books_df, new_books], ignore_index=True)
        return combined_books, current_page + 1, gr.update(visible=has_more), combined_books
    else:
        return current_books_df, current_page, gr.update(visible=False), current_books_df

def load_more_popular(current_page, current_books_df):
    new_books, has_more = get_popular_books(current_page)
    
    if not new_books.empty:
        combined_books = pd.concat([current_books_df, new_books], ignore_index=True)
        return combined_books, current_page + 1, gr.update(visible=has_more), combined_books
    else:
        return current_books_df, current_page, gr.update(visible=False), current_books_df

def refresh_random(query):
    random_books, random_has_more = search_books(query, 0)
    return random_books, 1, gr.update(visible=random_has_more), random_books

def clear_search():
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
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }
    .book-btn {
        width: 150px !important;
        height: 60px !important;
        padding: 8px !important;
        font-size: 12px !important;
        line-height: 1.2 !important;
        white-space: normal !important;
        word-wrap: break-word !important;
        text-align: center !important;
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
    .search-row {
        margin-bottom: 20px;
    }
""") as demo:

    gr.Markdown("# 📚 Book Explorer")
    
    # Book Details Modal
    with Modal("📖 Book Details", visible=False) as modal:
        book_details_html = gr.HTML()
        close_btn = gr.Button("Close", variant="secondary")
    
    with gr.Row(elem_classes="search-row"):
        search_box = gr.Textbox(
            label="",
            placeholder="🔍 Search books by title, author, or genre...",
            scale=4
        )
        clear_btn = gr.Button("Clear", scale=1)
    
    # Random Books Section
    with gr.Column(elem_classes="container") as random_section:
        with gr.Row(elem_classes="section-header"):
            random_title = gr.Markdown()
            refresh_btn = gr.Button("🔄 Refresh")
        
        random_display = gr.Column(elem_classes="books-container")
        
        with gr.Row(elem_classes="load-more-btn"):
            load_random_btn = gr.Button("📚 Load More Books", visible=True)
            random_page = gr.State(1)
            random_loaded_books = gr.State(pd.DataFrame())
    
    # Popular Books Section  
    with gr.Column(elem_classes="container") as popular_section:
        with gr.Row(elem_classes="section-header"):
            gr.Markdown("📚 Popular Books")
        
        popular_display = gr.Column(elem_classes="books-container")
        
        with gr.Row(elem_classes="load-more-btn"):
            load_popular_btn = gr.Button("📚 Load More Books", visible=True)
            popular_page = gr.State(1)
            popular_loaded_books = gr.State(pd.DataFrame())

    # Store button references
    random_buttons_ref = gr.State([])
    popular_buttons_ref = gr.State([])

    def update_random_display(random_books):
        """Update random books display with buttons"""
        with random_display:
            random_display.__init__()  # Clear previous content
            buttons = []
            for _, row in random_books.iterrows():
                btn, book_id = create_book_button(row)
                buttons.append((btn, book_id))
            return buttons

    def update_popular_display(popular_books):
        """Update popular books display with buttons"""
        with popular_display:
            popular_display.__init__()  # Clear previous content
            buttons = []
            for _, row in popular_books.iterrows():
                btn, book_id = create_book_button(row)
                buttons.append((btn, book_id))
            return buttons

    # Event handlers
    def handle_search(query):
        random_books, popular_books, r_page, p_page, r_has_more, p_has_more, r_title, r_loaded, p_loaded = initial_state(query)
        random_buttons = update_random_display(random_books)
        popular_buttons = update_popular_display(popular_books)
        return random_buttons, popular_buttons, r_page, p_page, r_has_more, p_has_more, r_title, r_loaded, p_loaded

    search_box.submit(
        handle_search,
        [search_box],
        [random_buttons_ref, popular_buttons_ref, random_page, popular_page, load_random_btn, load_popular_btn, random_title, random_loaded_books, popular_loaded_books]
    )
    
    # Connect buttons to modal
    def connect_buttons(buttons, buttons_ref):
        """Connect all buttons to show modal"""
        for btn, book_id in buttons:
            btn.click(
                show_book_details,
                inputs=[gr.State(book_id)],
                outputs=[modal, book_details_html]
            )
        return buttons

    # Close modal
    close_btn.click(
        lambda: gr.update(visible=False),
        None,
        [modal]
    )

    # Initial load
    def load_initial():
        random_books, popular_books, r_page, p_page, r_has_more, p_has_more, r_title, r_loaded, p_loaded = initial_state()
        random_buttons = update_random_display(random_books)
        popular_buttons = update_popular_display(popular_books)
        return random_buttons, popular_buttons, r_page, p_page, r_has_more, p_has_more, r_title, r_loaded, p_loaded

    demo.load(
        load_initial,
        [],
        [random_buttons_ref, popular_buttons_ref, random_page, popular_page, load_random_btn, load_popular_btn, random_title, random_loaded_books, popular_loaded_books]
    )

demo.launch()