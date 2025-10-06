import ast
import pandas as pd
import gradio as gr
from gradio_modal import Modal
import random

# ---------- Load dataset ----------
df = pd.read_csv("data_mini_books.csv")
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

BOOKS_PER_LOAD = 6

# ---------- Helpers ----------
def show_book_details(book_id):
    book = df[df["id"] == book_id].iloc[0]
    html = f"""
    <div style="text-align:center; max-height: 80vh; overflow-y:auto;">
        <img src="{book['image_url']}" style="width:180px;height:auto;border-radius:8px;margin-bottom:10px;">
        <h2>{book['title']}</h2>
        <h4>by {', '.join(book['authors'])}</h4>
        <p><strong>Genres:</strong> {', '.join(book['genres'])}</p>
        <p>{book.get('description','No description available.')}</p>
    </div>
    """
    # Also move modal near scroll with JS hack
    js_move_modal = """
    <script>
    const modal = document.querySelector('.gr-modal');
    if(modal) {
        const scrollY = window.scrollY || window.pageYOffset;
        modal.style.top = (scrollY + window.innerHeight/4) + "px";
    }
    </script>
    """
    return gr.update(visible=True), html + js_move_modal

def create_book_buttons(df_subset):
    buttons = []
    for _, book in df_subset.iterrows():
        btn = gr.Button(book["title"], elem_classes="book-card-btn")
        buttons.append((btn, book["id"]))
    return buttons

# ---------- Gradio UI ----------
with gr.Blocks(css="""
.book-card-btn { margin:5px; width:150px; height:50px; }
.books-container { max-height:400px; overflow-y:auto; border:1px solid #ddd; padding:10px; display:flex; flex-wrap:wrap; }
.section { margin-bottom:20px; }
""") as demo:

    gr.Markdown("# 📚 Book Explorer with Scroll-Aware Modal")

    # ---------- Modal ----------
    with Modal("Book Details", visible=False) as book_modal:
        book_detail_html = gr.HTML()
        close_modal_btn = gr.Button("❌ Close")
    close_modal_btn.click(lambda: gr.update(visible=False), None, book_modal)

    # ---------- Random Books ----------
    with gr.Column(elem_classes="section"):
        gr.Markdown("🎲 Random Books")
        random_display_container = gr.Column(elem_classes="books-container")
        initial_random_books = df.sample(frac=1).reset_index(drop=True).iloc[:BOOKS_PER_LOAD]
        buttons = create_book_buttons(initial_random_books)
        for btn, book_id in buttons:
            btn.click(show_book_details, inputs=[gr.State(book_id)], outputs=[book_modal, book_detail_html])

    # ---------- Popular Books ----------
    with gr.Column(elem_classes="section"):
        gr.Markdown("📚 Popular Books")
        popular_display_container = gr.Column(elem_classes="books-container")
        initial_popular_books = df.head(BOOKS_PER_LOAD)
        buttons = create_book_buttons(initial_popular_books)
        for btn, book_id in buttons:
            btn.click(show_book_details, inputs=[gr.State(book_id)], outputs=[book_modal, book_detail_html])

demo.launch()
