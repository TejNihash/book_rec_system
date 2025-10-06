import ast
import pandas as pd
import gradio as gr
from gradio_modal import Modal
import random

# ---------- Load dataset ----------
df = pd.read_csv("data_mini_books.csv")

# Ensure unique ID column
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

# Convert string lists
df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# Lowercase versions for search
df["title_lower"] = df["title"].str.lower()
df["authors_lower"] = df["authors"].apply(lambda lst: [a.lower() for a in lst])
df["genres_lower"] = df["genres"].apply(lambda lst: [g.lower() for g in lst])

BOOKS_PER_LOAD = 12

# ---------- Search / Pagination ----------
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

# ---------- Book Cards ----------
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
    return f"""
    <script>
        let selectedBookId = "";
        function selectBook(book_id) {{
            selectedBookId = book_id;
            document.getElementById("hidden_modal_btn").click();
        }}
    </script>
    <div class="books-grid">{books_html}</div>
    """

# ---------- State Functions ----------
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

# ---------- Book Details Function ----------
def show_book_details():
    global selectedBookId
    book = df[df["id"].astype(str)==str(selectedBookId)].iloc[0]
    html = f"""
    <div style="text-align:center;">
        <img src="{book['image_url']}" style="width:180px;height:auto;border-radius:8px;margin-bottom:10px;">
        <h2>{book['title']}</h2>
        <h4>by {', '.join(book['authors'])}</h4>
        <p><strong>Genres:</strong> {', '.join(book['genres'])}</p>
        <p style="margin-top:10px;">{book.get('description','No description available.')}</p>
    </div>
    """
    return gr.update(visible=True), html

# ---------- Gradio UI ----------
with gr.Blocks(css=""" 
/* Paste your CSS here for .book-card, .books-grid, scrollbars, etc. */
""") as demo:

    gr.Markdown("# 📚 Book Explorer")

    # Hidden button for modal trigger
    hidden_modal_btn = gr.Button(visible=False, elem_id="hidden_modal_btn")

    # Search row
    with gr.Row():
        search_box = gr.Textbox(placeholder="🔍 Search books by title, author, or genre...", scale=4)
        clear_btn = gr.Button("Clear", scale=1)

    # Random books
    with gr.Column():
        with gr.Row():
            random_title = gr.Markdown("🎲 Discover Random Books")
            refresh_btn = gr.Button("🔄 Refresh")
        random_display = gr.HTML()
        with gr.Row():
            load_random_btn = gr.Button("📚 Load More Books", visible=True)
            random_page = gr.State(1)
            random_loaded_books = gr.State(pd.DataFrame())

    # Popular books
    with gr.Column():
        gr.Markdown("📚 Popular Books")
        popular_display = gr.HTML()
        with gr.Row():
            load_popular_btn = gr.Button("📚 Load More Books", visible=True)
            popular_page = gr.State(1)
            popular_loaded_books = gr.State(pd.DataFrame())

    # Modal
    with Modal("Book Details", visible=False) as book_modal:
        book_detail_html = gr.HTML()
        close_modal_btn = gr.Button("❌ Close")

    # ---------- Event Handlers ----------
    search_box.submit(initial_state, [search_box], [random_display, popular_display, random_page, popular_page, load_random_btn, load_popular_btn, random_title, random_loaded_books, popular_loaded_books])
    load_random_btn.click(load_more_random, [search_box, random_page, random_loaded_books], [random_display, random_page, load_random_btn, random_loaded_books])
    load_popular_btn.click(load_more_popular, [popular_page, popular_loaded_books], [popular_display, popular_page, load_popular_btn, popular_loaded_books])
    refresh_btn.click(refresh_random, [search_box], [random_display, random_page, load_random_btn, random_loaded_books])
    clear_btn.click(clear_search, [], [search_box, random_display, popular_display, random_page, popular_page, load_random_btn, load_popular_btn, random_title, random_loaded_books, popular_loaded_books])
    demo.load(initial_state, [search_box], [random_display, popular_display, random_page, popular_page, load_random_btn, load_popular_btn, random_title, random_loaded_books, popular_loaded_books])

    # Book modal trigger
    hidden_modal_btn.click(show_book_details, [], [book_modal, book_detail_html])
    close_modal_btn.click(lambda: gr.update(visible=False), None, book_modal)

demo.launch()
