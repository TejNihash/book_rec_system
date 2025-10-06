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

BOOKS_PER_LOAD = 6  # adjust as needed

# ---------- Helper ----------
def show_book_details(book_id):
    book = df[df["id"] == book_id].iloc[0]
    html = f"""
    <div style="text-align:center;">
        <img src="{book['image_url']}" style="width:180px;height:auto;border-radius:8px;margin-bottom:10px;">
        <h2>{book['title']}</h2>
        <h4>by {', '.join(book['authors'])}</h4>
        <p><strong>Genres:</strong> {', '.join(book['genres'])}</p>
        <p>{book.get('description','No description available.')}</p>
    </div>
    """
    return gr.update(visible=True), html

def get_books_page(df_subset, page):
    start_idx = page * BOOKS_PER_LOAD
    end_idx = start_idx + BOOKS_PER_LOAD
    return df_subset.iloc[start_idx:end_idx], len(df_subset) > end_idx

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

    close_modal_btn.click(lambda: gr.update(visible=False), None, book_modal)

    # ---------- Search ----------
    with gr.Row():
        search_box = gr.Textbox(placeholder="🔍 Search books by title, author, or genre...", scale=4)
        clear_btn = gr.Button("Clear")

    # ---------- Random Books ----------
    with gr.Column(elem_classes="section"):
        gr.Markdown("🎲 Random Books")
        random_display_container = gr.Column(elem_classes="books-container")
        load_random_btn = gr.Button("📚 Load More Random Books")
        random_page = gr.State(0)
        random_loaded_books = gr.State(pd.DataFrame())

    # ---------- Popular Books ----------
    with gr.Column(elem_classes="section"):
        gr.Markdown("📚 Popular Books")
        popular_display_container = gr.Column(elem_classes="books-container")
        load_popular_btn = gr.Button("📚 Load More Popular Books")
        popular_page = gr.State(0)
        popular_loaded_books = gr.State(pd.DataFrame())

    # ---------- Functions to populate grids ----------
    def create_book_buttons(df_subset):
        """Return a list of gr.Buttons and their IDs"""
        buttons = []
        for _, book in df_subset.iterrows():
            btn = gr.Button(book["title"], elem_classes="book-card-btn")
            buttons.append((btn, book["id"]))
        return buttons

    def display_books(container, books_df):
        """Populate a column with book buttons"""
        with container:
            buttons = create_book_buttons(books_df)
            for btn, book_id in buttons:
                btn.click(show_book_details, inputs=[gr.State(book_id)], outputs=[book_modal, book_detail_html])
        return buttons

    # ---------- Initialize Random and Popular ----------
    initial_random_books = df.sample(frac=1).reset_index(drop=True).iloc[:BOOKS_PER_LOAD]
    random_loaded_books.set(initial_random_books)
    random_page.set(1)
    display_books(random_display_container, initial_random_books)

    initial_popular_books = df.head(BOOKS_PER_LOAD)
    popular_loaded_books.set(initial_popular_books)
    popular_page.set(1)
    display_books(popular_display_container, initial_popular_books)

demo.launch()
