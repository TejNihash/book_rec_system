import ast
import pandas as pd
import gradio as gr

# ---------- Load dataset ----------
df = pd.read_csv("data_mini_books.csv")
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

BOOKS_PER_LOAD = 6

# ---------- Helpers ----------
def collapse_book_card(title, authors):
    """Collapsed view HTML"""
    return f"<b>{title}</b><br><small>{', '.join(authors)}</small>"

def expand_book_card(book_id):
    """Expanded view HTML"""
    book = df[df["id"] == book_id].iloc[0]
    html = f"""
    <div style="text-align:center;">
        <img src="{book['image_url']}" style="width:120px;height:auto;margin-bottom:5px;">
        <h3>{book['title']}</h3>
        <p><em>{', '.join(book['authors'])}</em></p>
        <p><strong>Genres:</strong> {', '.join(book['genres'])}</p>
        <p>{book.get('description','No description available.')}</p>
    </div>
    """
    return html

# ---------- Gradio UI ----------
with gr.Blocks(css="""
.book-card { 
    border:1px solid #ccc; padding:10px; border-radius:8px; margin:5px; 
    width:160px; text-align:center; cursor:pointer; transition: all 0.2s; 
}
.book-card:hover { box-shadow:0 2px 8px rgba(0,0,0,0.15); }
.books-container { display:flex; flex-wrap:wrap; max-height:400px; overflow-y:auto; }
""") as demo:

    gr.Markdown("# 📚 Expandable Book Cards")

    # ---------- Random Books ----------
    gr.Markdown("🎲 Random Books")
    random_display_container = gr.Column(elem_classes="books-container")
    random_books = df.sample(frac=1).reset_index(drop=True).iloc[:BOOKS_PER_LOAD]

    for _, book in random_books.iterrows():
        card_html = gr.HTML(value=collapse_book_card(book['title'], book['authors']), elem_classes="book-card")
        card_html.click(fn=lambda bid=book['id']: expand_book_card(bid), inputs=[], outputs=card_html)

    # ---------- Popular Books ----------
    gr.Markdown("📚 Popular Books")
    popular_display_container = gr.Column(elem_classes="books-container")
    popular_books = df.head(BOOKS_PER_LOAD)

    for _, book in popular_books.iterrows():
        card_html = gr.HTML(value=collapse_book_card(book['title'], book['authors']), elem_classes="book-card")
        card_html.click(fn=lambda bid=book['id']: expand_book_card(bid), inputs=[], outputs=card_html)

demo.launch()
