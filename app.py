import ast
import pandas as pd
import gradio as gr
from gradio_modal import Modal

# ---------- Load dataset ----------
df = pd.read_csv("data_mini_books.csv")
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

BOOKS_PER_LOAD = 6  # per row demo

# ---------- Helpers ----------
def create_book_button(book):
    """Return a Gradio Button that triggers modal with book details"""
    return gr.Button(book["title"], elem_classes="book-card-btn"), book["id"]

def show_book_details(book_id):
    book = df[df["id"] == book_id].iloc[0]
    html = f"""
    <div style="text-align:center;">
        <img src="{book['image_url']}" style="width:180px;height:auto;border-radius:8px;margin-bottom:10px;">
        <h2>{book['title']}</h2>
        <h4>by {', '.join(book['authors'])}</h4>
        <p><strong>Genres:</strong> {', '.join(book['genres'])}</p>
        <p>{book.get('description', 'No description available.')}</p>
    </div>
    """
    return gr.update(visible=True), html

# ---------- Search / Pagination ----------
def search_books(query, page=0):
    query = query.strip().lower()
    if query:
        mask_title = df["title"].str.lower().str.contains(query)
        mask_authors = df["authors"].apply(lambda lst: any(query in a.lower() for a in lst))
        mask_genres = df["genres"].apply(lambda lst: any(query in g.lower() for g in lst))
        filtered = df[mask_title | mask_authors | mask_genres]
    else:
        filtered = df.sample(frac=1).reset_index(drop=True)
    start_idx = page * BOOKS_PER_LOAD
    end_idx = start_idx + BOOKS_PER_LOAD
    return filtered.iloc[start_idx:end_idx], len(filtered) > end_idx

def load_more_books(page, current_df, query="", section="random"):
    if section == "random":
        new_books, has_more = search_books(query, page)
    else:
        start_idx = page * BOOKS_PER_LOAD
        end_idx = start_idx + BOOKS_PER_LOAD
        new_books = df.iloc[start_idx:end_idx]
        has_more = len(df) > end_idx
    combined = pd.concat([current_df, new_books], ignore_index=True)
    return combined, page+1, has_more

# ---------- Gradio UI ----------
with gr.Blocks(css="""
/* minimal styling for demo */
.book-card-btn { margin:5px; width:150px; height:50px; }
.books-container { max-height:400px; overflow-y:auto; border:1px solid #ddd; padding:10px; }
.section { margin-bottom:20px; }
""") as demo:

    gr.Markdown("# 📚 Book Explorer with Modal")

    # ---------- Modal ----------
    with Modal("Book Details", visible=False) as book_modal:
        book_detail_html = gr.HTML()
        close_modal_btn = gr.Button("❌ Close")

    # ---------- Search ----------
    with gr.Row():
        search_box = gr.Textbox(placeholder="🔍 Search books by title, author, or genre...", scale=4)
        clear_btn = gr.Button("Clear")

    # ---------- Random Books ----------
    with gr.Column(elem_classes="section"):
        gr.Markdown("🎲 Random Books")
        random_display = gr.HTML(elem_classes="books-container")
        load_random_btn = gr.Button("📚 Load More Random Books")
        random_page = gr.State(0)
        random_loaded_books = gr.State(pd.DataFrame())

    # ---------- Popular Books ----------
    with gr.Column(elem_classes="section"):
        gr.Markdown("📚 Popular Books")
        popular_display = gr.HTML(elem_classes="books-container")
        load_popular_btn = gr.Button("📚 Load More Popular Books")
        popular_page = gr.State(0)
        popular_loaded_books = gr.State(pd.DataFrame())

    # ---------- Event Handlers ----------
    # Load initial random books
    def init_random():
        books, has_more = search_books("", 0)
        return create_book_buttons_html(books), 1, books
    def init_popular():
        books = df.iloc[:BOOKS_PER_LOAD]
        return create_book_buttons_html(books), 1, books

    def create_book_buttons_html(books_df):
        html_parts = []
        for idx, row in books_df.iterrows():
            html_parts.append(f"""
            <button class="book-card-btn" onclick="document.getElementById('hidden_book_id').value='{row['id']}';document.getElementById('hidden_btn').click();">{row['title']}</button>
            """)
        return "<div>" + "".join(html_parts) + "</div>"

    # Hidden inputs to trigger modal
    hidden_book_id = gr.Textbox(visible=False, elem_id="hidden_book_id")
    hidden_btn = gr.Button(visible=False, elem_id="hidden_btn")

    def show_book_from_hidden(book_id):
        return show_book_details(book_id)

    hidden_btn.click(show_book_from_hidden, [hidden_book_id], [book_modal, book_detail_html])
    close_modal_btn.click(lambda: gr.update(visible=False), None, book_modal)

    # Load initial content
    random_display.update(init_random()[0])
    popular_display.update(init_popular()[0])

demo.launch()
