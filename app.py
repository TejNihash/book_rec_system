import ast
import pandas as pd
import gradio as gr
from gradio_modal import Modal

# Load dataset
df = pd.read_csv("data_mini_books.csv")
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

BOOKS_PER_LOAD = 6  # For demo

# ---------- Helpers ----------
def create_book_button(book):
    """Return a Gradio Button that triggers modal with book details"""
    return gr.Button(book["title"]), book["id"]

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

# ---------- UI ----------
with gr.Blocks() as demo:
    gr.Markdown("# 📚 Book Explorer with Modal Details")

    # Random books demo
    with gr.Row():
        random_books_buttons = []
        for idx, row in df.head(BOOKS_PER_LOAD).iterrows():
            btn, book_id = create_book_button(row)
            random_books_buttons.append((btn, book_id))

    # Modal for book details
    with Modal("Book Details", visible=False) as book_modal:
        book_detail_html = gr.HTML()
        close_modal_btn = gr.Button("❌ Close")

    # Connect buttons to modal
    for btn, book_id in random_books_buttons:
        btn.click(show_book_details, inputs=[gr.State(book_id)], outputs=[book_modal, book_detail_html])

    close_modal_btn.click(lambda: gr.update(visible=False), None, book_modal)

demo.launch()
