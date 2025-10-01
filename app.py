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
        filtered = df
    
    # Pagination
    start_idx = page * BOOKS_PER_LOAD
    end_idx = start_idx + BOOKS_PER_LOAD
    page_books = filtered.iloc[start_idx:end_idx]
    
    has_more = len(page_books) == BOOKS_PER_LOAD and end_idx < len(filtered)
    return page_books, has_more

def get_popular_books(page=0):
    """Get popular books with pagination"""
    start_idx = page * BOOKS_PER_LOAD
    end_idx = start_idx + BOOKS_PER_LOAD
    page_books = df.iloc[start_idx:end_idx]
    
    has_more = len(page_books) == BOOKS_PER_LOAD and end_idx < len(df)
    return page_books, has_more

def create_book_card(img_url, title, authors, genres):
    """Create a book card"""
    return f"""
    <div class="book-card">
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
        create_book_card(row["image_url"], row["title"], row["authors"], row["genres"])
        for _, row in books_df.iterrows()
    ])
    
    return f'<div class="books-grid">{books_html}</div>'

# Initial state
def initial_state(query=""):
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
        0, 0,  # page states
        gr.update(visible=random_has_more), 
        gr.update(visible=popular_has_more),
        results_text
    )

# Load more functions
def load_more_random(query, current_page, current_display):
    new_page = current_page + 1
    random_books, has_more = search_books(query, new_page)
    new_display = create_books_display(random_books)
    
    # Combine displays
    combined_display = current_display.replace('</div>', '') + new_display.replace('<div class="books-grid">', '') + '</div>'
    
    return combined_display, new_page, gr.update(visible=has_more)

def load_more_popular(current_page, current_display):
    new_page = current_page + 1
    popular_books, has_more = get_popular_books(new_page)
    new_display = create_books_display(popular_books)
    
    # Combine displays
    combined_display = current_display.replace('</div>', '') + new_display.replace('<div class="books-grid">', '') + '</div>'
    
    return combined_display, new_page, gr.update(visible=has_more)

# Refresh random
def refresh_random(query):
    return load_more_random(query, -1, "")  # -1 so it becomes page 0

# Clear search
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
        grid-template-columns: repeat(6, 1fr);
        gap: 15px;
    }
    .book-card {
        background: white;
        border-radius: 8px;
        padding: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        text-align: center;
        height: 260px;
        display: flex;
        flex-direction: column;
    }
    .book-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    .book-card img {
        width: 100%;
        height: 150px;
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
        width: 6px;
    }
    .books-container::-webkit-scrollbar-track {
        background: #f1f1f1;
    }
    .books-container::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 3px;
    }
""") as demo:

    gr.Markdown("# 📚 Book Explorer")
    
    with gr.Row():
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
            random_page = gr.State(0)
    
    # Popular Books Section  
    with gr.Column(elem_classes="container"):
        with gr.Row(elem_classes="section-header"):
            gr.Markdown("📚 Popular Books")
        
        popular_display = gr.HTML(elem_classes="books-container")
        
        with gr.Row(elem_classes="load-more-btn"):
            load_popular_btn = gr.Button("📚 Load More Books", visible=True)
            popular_page = gr.State(0)

    # Event handlers
    search_box.submit(
        initial_state,
        [search_box],
        [random_display, popular_display, random_page, popular_page, load_random_btn, load_popular_btn, random_title]
    )
    
    load_random_btn.click(
        load_more_random,
        [search_box, random_page, random_display],
        [random_display, random_page, load_random_btn]
    )
    
    load_popular_btn.click(
        load_more_popular,
        [popular_page, popular_display],
        [popular_display, popular_page, load_popular_btn]
    )
    
    refresh_btn.click(
        refresh_random,
        [search_box],
        [random_display, random_page, load_random_btn]
    )
    
    clear_btn.click(
        clear_search,
        [],
        [search_box, random_display, popular_display, random_page, popular_page, load_random_btn, load_popular_btn, random_title]
    )

    demo.load(
        initial_state,
        [search_box],
        [random_display, popular_display, random_page, popular_page, load_random_btn, load_popular_btn, random_title]
    )

demo.launch()