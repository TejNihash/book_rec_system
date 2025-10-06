import ast
import pandas as pd
import gradio as gr
from gradio_modal import Modal
import random

# Load dataset
df = pd.read_csv("data_mini_books.csv")

# Ensure ID column exists
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

# Convert string lists to Python lists
df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# Lowercase columns for search
df["title_lower"] = df["title"].str.lower()
df["authors_lower"] = df["authors"].apply(lambda lst: [a.lower() for a in lst])
df["genres_lower"] = df["genres"].apply(lambda lst: [g.lower() for g in lst])

BOOKS_PER_LOAD = 12

# --------- Search / Pagination ---------
def search_books(query, page=0):
    query = query.strip().lower()
    if query:
        mask_title = df["title_lower"].str.contains(query, na=False)
        mask_authors = df["authors_lower"].apply(lambda lst: any(query in a for a in lst))
        mask_genres = df["genres_lower"].apply(lambda lst: any(query in g for g in lst))
        filtered = df[mask_title | mask_authors | mask_genres]
    else:
        filtered = df.sample(frac=1).reset_index(drop=True)
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

# --------- Book Cards / Display ---------
def create_book_card(book_id, img_url, title, authors, genres):
    return f"""
    <div class="book-card" onclick="selectBook('{book_id}')">
        <img src="{img_url}" onerror="this.src='https://via.placeholder.com/150x220/667eea/white?text=No+Image'">
        <div class="book-info">
            <div class="title">{title}</div>
            <div class="authors">by {', '.join(authors)}</div>
            <div class="genres">{', '.join(genres[:2])}</div>
        </div>
    </div>
    """

def create_books_display(books_df):
    if books_df.empty:
        return "<div class='no-books'>No books found</div>"

    books_html = "".join([
        create_book_card(row["id"], row["image_url"], row["title"], row["authors"], row["genres"])
        for _, row in books_df.iterrows()
    ])

    # JS hook to trigger hidden textbox
    return f"""
    <script>
        function selectBook(book_id) {{
            const el = window.gradioApp().querySelector('#book_select textarea');
            el.value = book_id;
            el.dispatchEvent(new Event('input'));
        }}
    </script>
    <div class="books-grid">{books_html}</div>
    """

# --------- State Functions ---------
def initial_state(query=""):
    random_books, random_has_more = search_books(query, 0)
    popular_books, popular_has_more = get_popular_books(0)
    results_text = f"🎲 Showing results for '{query}'" if query else "🎲 Discover Random Books"
    return (
        create_books_display(random_books),
        create_books_display(popular_books),
        1, 1,
        gr.update(visible=random_has_more),
        gr.update(visible=popular_has_more),
        results_text,
        random_books,
        popular_books
    )

def load_more_random(query, page, current_books_df):
    new_books, has_more = search_books(query, page)
    combined_books = pd.concat([current_books_df, new_books], ignore_index=True) if not new_books.empty else current_books_df
    return create_books_display(combined_books), page + 1, gr.update(visible=has_more), combined_books

def load_more_popular(page, current_books_df):
    new_books, has_more = get_popular_books(page)
    combined_books = pd.concat([current_books_df, new_books], ignore_index=True) if not new_books.empty else current_books_df
    return create_books_display(combined_books), page + 1, gr.update(visible=has_more), combined_books

def refresh_random(query):
    books, has_more = search_books(query, 0)
    return create_books_display(books), 1, gr.update(visible=has_more), books

def clear_search():
    return "", *initial_state("")

# --------- Book Details Modal ---------
def show_book_details(book_id):
    if not book_id:
        return gr.update(visible=False), ""
    book = df[df["id"].astype(str) == str(book_id)].iloc[0]
    detail_html = f"""
    <div style="text-align:center;">
        <img src="{book['image_url']}" style="width:180px;height:auto;border-radius:8px;margin-bottom:10px;">
        <h2>{book['title']}</h2>
        <h4>by {', '.join(book['authors'])}</h4>
        <p><strong>Genres:</strong> {', '.join(book['genres'])}</p>
        <p style="margin-top:10px;">{book.get('description','No description available.')}</p>
    </div>
    """
    return gr.update(visible=True), detail_html

# --------- Gradio UI ---------
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
    .modal-overlay {
        background: rgba(0,0,0,0.5);
    }
    .modal-content {
        max-width: 800px;
        max-height: 80vh;
        overflow-y: auto;
    }
""") as demo:

    gr.Markdown("# 📚 Book Explorer")

    # Hidden textbox for JS -> Python communication
    book_select = gr.Textbox(visible=False, elem_id="book_select")

    # Search Row
    with gr.Row():
        search_box = gr.Textbox(placeholder="🔍 Search books by title, author, or genre...", scale=4)
        clear_btn = gr.Button("Clear", scale=1)

    # Random Books Section
    with gr.Column():
        with gr.Row():
            random_title = gr.Markdown("🎲 Discover Random Books")
            refresh_btn = gr.Button("🔄 Refresh")
        random_display = gr.HTML()
        with gr.Row():
            load_random_btn = gr.Button("📚 Load More Books", visible=True)
            random_page = gr.State(1)
            random_loaded_books = gr.State(pd.DataFrame())

    # Popular Books Section
    with gr.Column():
        gr.Markdown("📚 Popular Books")
        popular_display = gr.HTML()
        with gr.Row():
            load_popular_btn = gr.Button("📚 Load More Books", visible=True)
            popular_page = gr.State(1)
            popular_loaded_books = gr.State(pd.DataFrame())

    # Modal for Book Details
    with Modal("Book Details", visible=False) as book_modal:
        book_detail_html = gr.HTML()
        close_modal_btn = gr.Button("❌ Close")

    # Event handlers
    search_box.submit(initial_state, [search_box], [random_display, popular_display, random_page, popular_page, load_random_btn, load_popular_btn, random_title, random_loaded_books, popular_loaded_books])
    load_random_btn.click(load_more_random, [search_box, random_page, random_loaded_books], [random_display, random_page, load_random_btn, random_loaded_books])
    load_popular_btn.click(load_more_popular, [popular_page, popular_loaded_books], [popular_display, popular_page, load_popular_btn, popular_loaded_books])
    refresh_btn.click(refresh_random, [search_box], [random_display, random_page, load_random_btn, random_loaded_books])
    clear_btn.click(clear_search, [], [search_box, random_display, popular_display, random_page, popular_page, load_random_btn, load_popular_btn, random_title, random_loaded_books, popular_loaded_books])
    demo.load(initial_state, [search_box], [random_display, popular_display, random_page, popular_page, load_random_btn, load_popular_btn, random_title, random_loaded_books, popular_loaded_books])

    # Book click triggers modal
    book_select.change(show_book_details, [book_select], [book_modal, book_detail_html])
    close_modal_btn.click(lambda: gr.update(visible=False), None, book_modal)

demo.launch()
