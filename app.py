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
BOOKS_PER_LOAD = 6  # Smaller for demo

def search_books(query, page=0):
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
    start_idx = page * BOOKS_PER_LOAD
    end_idx = start_idx + BOOKS_PER_LOAD
    page_books = df.iloc[start_idx:end_idx]
    
    has_more = len(df) > end_idx
    return page_books, has_more

def get_book_details(book_id):
    """Get book details for display"""
    book = df[df["id"] == book_id].iloc[0]
    
    details = f"""
    <div style="padding: 20px;">
        <div style="display: grid; grid-template-columns: 200px 1fr; gap: 20px; align-items: start;">
            <div>
                <img src="{book['image_url']}" 
                     style="width: 100%; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);"
                     onerror="this.src='https://via.placeholder.com/200x300/667eea/white?text=No+Image'">
            </div>
            <div>
                <h2 style="margin: 0 0 10px 0; color: #2c3e50;">{book['title']}</h2>
                <p style="margin: 5px 0; color: #666;"><strong>Author(s):</strong> {', '.join(book['authors'])}</p>
                <p style="margin: 5px 0; color: #666;"><strong>Genres:</strong> {', '.join(book['genres'])}</p>
                <p style="margin: 5px 0; color: #666;"><strong>Published:</strong> {book.get('published_year', 'Unknown')}</p>
                <p style="margin: 5px 0; color: #666;"><strong>Rating:</strong> {book.get('average_rating', 'Not rated')}</p>
                <p style="margin: 5px 0; color: #666;"><strong>Pages:</strong> {book.get('num_pages', 'Unknown')}</p>
                <div style="margin-top: 20px;">
                    <h4 style="margin: 0 0 10px 0; color: #2c3e50;">Description</h4>
                    <p style="line-height: 1.6; color: #555;">{book.get('description', 'No description available.')}</p>
                </div>
            </div>
        </div>
    </div>
    """
    return details

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
    .book-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        gap: 15px;
    }
    .book-card {
        background: white;
        border-radius: 8px;
        padding: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
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
    .book-title {
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
    .book-authors {
        font-size: 10px;
        color: #666;
        margin-bottom: 3px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .book-genres {
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
    .load-more-btn {
        display: flex;
        justify-content: center;
        margin-top: 10px;
    }
""") as demo:

    gr.Markdown("# 📚 Book Explorer")
    
    # State
    selected_book_id = gr.State(None)
    current_random_books = gr.State(pd.DataFrame())
    current_popular_books = gr.State(pd.DataFrame())
    
    with gr.Row():
        search_box = gr.Textbox(
            label="",
            placeholder="🔍 Search books by title, author, or genre...",
            scale=4
        )
        clear_btn = gr.Button("Clear", scale=1)
    
    # Main view vs Detail view
    with gr.Column(visible=True) as main_view:
        # Random Books Section
        with gr.Column(elem_classes="container") as random_section:
            with gr.Row(elem_classes="section-header"):
                random_title = gr.Markdown("🎲 Discover Random Books")
                refresh_btn = gr.Button("🔄 Refresh")
            
            random_display = gr.HTML()
            
            with gr.Row(elem_classes="load-more-btn"):
                load_random_btn = gr.Button("📚 Load More Books", visible=True)
        
        # Popular Books Section  
        with gr.Column(elem_classes="container") as popular_section:
            with gr.Row(elem_classes="section-header"):
                gr.Markdown("📚 Popular Books")
            
            popular_display = gr.HTML()
            
            with gr.Row(elem_classes="load-more-btn"):
                load_popular_btn = gr.Button("📚 Load More Books", visible=True)
    
    # Detail View
    with gr.Column(visible=False) as detail_view:
        gr.Markdown("## 📖 Book Details")
        book_details = gr.HTML()
        back_btn = gr.Button("← Back to Books")
    
    # Create book cards HTML
    def create_book_cards_html(books_df, section_name):
        if books_df.empty:
            return "<div style='text-align: center; padding: 40px; color: #666;'>No books found</div>"
        
        cards_html = []
        for _, book in books_df.iterrows():
            card_html = f"""
            <div class="book-card" onclick="selectBook('{book['id']}', '{section_name}')">
                <img src="{book['image_url']}" onerror="this.src='https://via.placeholder.com/150x220/667eea/white?text=No+Image'">
                <div class="book-title">{book['title']}</div>
                <div class="book-authors">by {', '.join(book['authors'])}</div>
                <div class="book-genres">{', '.join(book['genres'][:2])}</div>
            </div>
            """
            cards_html.append(card_html)
        
        return f'<div class="book-grid">{"".join(cards_html)}</div>'
    
    # JavaScript for book selection - FIXED: Better element finding
    demo.load(
        None,
        None,
        None,
        js="""
        function selectBook(bookId, sectionName) {
            // Find the hidden inputs by looking for hidden textboxes
            const hiddenInputs = document.querySelectorAll('input[type="text"]');
            let bookIdInput = null;
            let sectionInput = null;
            
            for (let input of hiddenInputs) {
                if (input.offsetParent === null) { // hidden element
                    if (!bookIdInput) {
                        bookIdInput = input;
                    } else if (!sectionInput) {
                        sectionInput = input;
                    }
                }
            }
            
            if (bookIdInput) {
                bookIdInput.value = bookId;
                bookIdInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
        """
    )
    
    # Hidden components for book selection
    selected_book_id = gr.Textbox(visible=False, elem_id="selected-book-id")
    selected_section = gr.Textbox(visible=False, elem_id="selected-section")
    
    # Update displays
    def update_displays(random_books, popular_books):
        random_html = create_book_cards_html(random_books, "random")
        popular_html = create_book_cards_html(popular_books, "popular")
        return random_html, popular_html, random_books, popular_books
    
    # Show book details
    def show_book_details(book_id):
        if not book_id:
            return gr.update(visible=True), gr.update(visible=False), ""
        
        details = get_book_details(book_id)
        return gr.update(visible=False), gr.update(visible=True), details
    
    # Back to main view
    def back_to_main():
        return gr.update(visible=True), gr.update(visible=False), ""
    
    # Search function
    def handle_search(query):
        random_books, _ = search_books(query, 0)
        popular_books, _ = get_popular_books(0)
        return update_displays(random_books, popular_books)
    
    # Event handlers
    search_box.submit(
        handle_search,
        [search_box],
        [random_display, popular_display, current_random_books, current_popular_books]
    )
    
    clear_btn.click(
        lambda: ("",) + handle_search(""),
        [],
        [search_box, random_display, popular_display, current_random_books, current_popular_books]
    )
    
    selected_book_id.input(
        show_book_details,
        [selected_book_id],
        [main_view, detail_view, book_details]
    )
    
    back_btn.click(
        back_to_main,
        [],
        [main_view, detail_view, book_details]
    )
    
    # Initial load
    def load_initial():
        random_books, _ = search_books("", 0)
        popular_books, _ = get_popular_books(0)
        return update_displays(random_books, popular_books)
    
    demo.load(
        load_initial,
        [],
        [random_display, popular_display, current_random_books, current_popular_books]
    )

demo.launch()