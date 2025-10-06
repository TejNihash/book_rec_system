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
def collapsed_card_html(title, authors):
    return f"""
    <div class='card-collapsed'>
        <b>{title}</b><br><small>{', '.join(authors)}</small>
    </div>
    """

def expanded_card_html(book_id):
    book = df[df["id"] == book_id].iloc[0]
    html = f"""
    <div class='card-expanded'>
        <img src="{book['image_url']}" style="width:120px;height:auto;border-radius:6px;margin-bottom:8px;">
        <h3>{book['title']}</h3>
        <p><em>{', '.join(book['authors'])}</em></p>
        <p><strong>Genres:</strong> {', '.join(book['genres'])}</p>
        <p>{book.get('description','No description available.')}</p>
    </div>
    """
    return html

# Toggle expand/collapse
def toggle_card(current_html, book_id):
    if "card-collapsed" in current_html:
        return expanded_card_html(book_id)
    else:
        book = df[df["id"] == book_id].iloc[0]
        return collapsed_card_html(book['title'], book['authors'])

# ---------- Gradio UI ----------
with gr.Blocks(css="""
.card-collapsed, .card-expanded { 
    border:1px solid #ccc; padding:10px; border-radius:8px; margin:5px; 
    cursor:pointer; transition: all 0.2s; width:200px; text-align:center;
    background:white;
}
.card-collapsed:hover { box-shadow:0 2px 8px rgba(0,0,0,0.15); }
.card-expanded { width:300px; text-align:center; box-shadow:0 4px 12px rgba(0,0,0,0.2); }
.books-container { display:flex; flex-wrap:wrap; max-height:400px; overflow-y:auto; }
""") as demo:

    gr.Markdown("# 📚 Expandable & Collapsible Book Cards")

    # ---------- Random Books ----------
    gr.Markdown("🎲 Random Books")
    random_container = gr.Column(elem_classes="books-container")
    random_books = df.sample(frac=1).reset_index(drop=True).iloc[:BOOKS_PER_LOAD]

    random_cards = []
    for _, book in random_books.iterrows():
        card = gr.HTML(value=collapsed_card_html(book['title'], book['authors']))
        card.click(fn=toggle_card, inputs=[card, gr.State(book['id'])], outputs=card)
        random_cards.append(card)

    # ---------- Popular Books ----------
    gr.Markdown("📚 Popular Books")
    popular_container = gr.Column(elem_classes="books-container")
    popular_books = df.head(BOOKS_PER_LOAD)

    popular_cards = []
    for _, book in popular_books.iterrows():
        card = gr.HTML(value=collapsed_card_html(book['title'], book['authors']))
        card.click(fn=toggle_card, inputs=[card, gr.State(book['id'])], outputs=card)
        popular_cards.append(card)

    # ---------- JS for ESC key to collapse all expanded cards ----------
    js_escape = """
    <script>
    document.addEventListener('keydown', function(event) {
        if(event.key === 'Escape') {
            let expanded = document.querySelectorAll('.card-expanded');
            expanded.forEach(card => {
                card.innerHTML = card.getAttribute('data-collapsed');
                card.classList.remove('card-expanded');
                card.classList.add('card-collapsed');
            });
        }
    });
    </script>
    """
    gr.HTML(js_escape)

demo.launch()
