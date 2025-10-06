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

def create_book_card(book_row, is_expanded=False):
    """Create a book card - SIMPLIFIED VERSION"""
    book_id = book_row["id"]
    title = book_row["title"]
    authors = book_row["authors"]
    genres = book_row["genres"]
    image_url = book_row["image_url"]
    
    if is_expanded:
        # Expanded view
        description = book_row.get("description", "No description available.")
        year = book_row.get("published_year", "Unknown")
        rating = book_row.get("average_rating", "Not rated")
        pages = book_row.get("num_pages", "Unknown")
        
        return f"""
        <div class="book-card expanded" id="book-{book_id}">
            <div class="expanded-content">
                <div class="expanded-left">
                    <img src="{image_url}" onerror="this.src='https://via.placeholder.com/200x300/667eea/white?text=No+Image'">
                    <div class="book-id" style="display:none;">{book_id}</div>
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
                    <button class="collapse-btn" onclick="window.collapseBook()">✕ Collapse</button>
                </div>
            </div>
        </div>
        """
    else:
        # Collapsed view
        return f"""
        <div class="book-card collapsed" id="book-{book_id}">
            <img src="{image_url}" onerror="this.src='https://via.placeholder.com/150x220/667eea/white?text=No+Image'">
            <div class="book-info">
                <div class="title">{title}</div>
                <div class="authors">by {', '.join(authors)}</div>
                <div class="genres">{', '.join(genres[:2])}</div>
                <button class="expand-btn" onclick="window.expandBook('{book_id}')">View Details</button>
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
    }
    .authors {
        font-size: 10px;
        color: #666;
        margin-bottom: 3px;
    }
    .genres {
        font-size: 9px;
        color: #888;
        font-style: italic;
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
    .expanded-left img {
        width: 100%;
        max-width: 200px;
        height: auto;
        margin-bottom: 15px;
    }
    .expanded-right h3 {
        margin: 0 0 10px 0;
        color: #2c3e50;
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
    .description p {
        line-height: 1.6;
        color: #555;
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
""") as demo:

    gr.Markdown("# 📚 Book Explorer")
    
    # DEBUG: Let's add some simple buttons to test if clicks work
    with gr.Row():
        test_btn = gr.Button("TEST CLICK - Does this work?")
        debug_output = gr.Textbox(label="Debug Output")
    
    def test_click():
        return "Yes! Clicks are working!"
    
    test_btn.click(test_click, None, debug_output)
    
    # Hidden component for book interactions
    selected_book = gr.Textbox(visible=False, label="Selected Book")
    collapse_all = gr.Button("Collapse", visible=False)
    
    # Simple book display for testing
    with gr.Column():
        gr.Markdown("## Simple Test Books")
        
        # Create a few test books as actual Gradio Buttons
        test_books = df.head(6)
        for _, book in test_books.iterrows():
            btn = gr.Button(
                f"{book['title'][:20]}...", 
                size="sm",
                elem_classes="test-book-btn"
            )
            
            def create_click_handler(book_id):
                def handler():
                    return f"Book {book_id} clicked!"
                return handler
            
            btn.click(
                create_click_handler(book["id"]),
                outputs=debug_output
            )

demo.launch()