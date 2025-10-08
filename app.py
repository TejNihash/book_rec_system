import ast
import pandas as pd
import gradio as gr

# ---------- Load dataset ----------
df = pd.read_csv("data_mini_books.csv")
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

BOOKS_PER_LOAD = 12

# ---------- Global favorites ----------
favorites_list = []

# ---------- Helper functions ----------
def toggle_favorite(book_id):
    global favorites_list
    book_match = df[df["id"] == book_id]
    if book_match.empty:
        return favorites_list
    book = book_match.iloc[0].to_dict()
    if any(f["id"] == book_id for f in favorites_list):
        favorites_list = [f for f in favorites_list if f["id"] != book_id]
    else:
        favorites_list.append(book)
    return favorites_list

def build_books_cards(books_df):
    cards = []
    for _, book in books_df.iterrows():
        with gr.Column():
            gr.Image(book["image_url"], elem_classes="book-img", show_label=False)
            gr.Markdown(f"**{book['title']}**")
            gr.Markdown(f"*by {', '.join(book['authors'])}*")
            btn = gr.Button("Add/Remove Favorite")
            btn.click(
                toggle_favorite,
                inputs=[gr.Textbox(value=book["id"], visible=False)],
                outputs=[favorites_container]
            )
    return cards

def render_favorites(favs):
    if not favs:
        return "<p>No favorites yet.</p>"
    html = ""
    for book in favs:
        html += f"""
        <div style="display:flex;gap:8px;margin-bottom:6px;align-items:center">
            <img src="{book['image_url']}" width="36" height="52"/>
            <div>
                <div style="font-weight:600">{book['title']}</div>
                <div style="font-size:12px;color:#555">by {', '.join(book['authors'])}</div>
            </div>
        </div>
        """
    return html

# ---------- Gradio UI ----------
with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column(scale=3):
            gr.Markdown("## 🎲 Random Books")
            random_books = df.sample(frac=1).head(12)
            for _, book in random_books.iterrows():
                with gr.Column():
                    gr.Image(book["image_url"], show_label=False)
                    gr.Markdown(f"**{book['title']}**")
                    gr.Markdown(f"*by {', '.join(book['authors'])}*")
                    book_id_input = gr.Textbox(value=book["id"], visible=False)
                    add_btn = gr.Button("Add/Remove Favorite")
                    add_btn.click(
                        toggle_favorite,
                        inputs=[book_id_input],
                        outputs=[]
                    )

        with gr.Column(scale=1):
            gr.Markdown("## ⭐ Favorites")
            favorites_container = gr.HTML("<p>No favorites yet.</p>")

demo.launch()
