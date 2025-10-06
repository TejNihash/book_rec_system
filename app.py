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
    <div class='card-collapsed' data-title="{title}" data-authors="{', '.join(authors)}">
        <b>{title}</b><br><small>{', '.join(authors)}</small>
    </div>
    """

def expanded_card_html(book_id):
    book = df[df["id"] == book_id].iloc[0]
    html = f"""
    <div class='card-expanded' data-title="{book['title']}" data-authors="{', '.join(book['authors'])}">
        <img src="{book['image_url']}" style="width:120px;height:auto;border-radius:6px;margin-bottom:8px;">
        <h3>{book['title']}</h3>
        <p><em>{', '.join(book['authors'])}</em></p>
        <p><strong>Genres:</strong> {', '.join(book['genres'])}</p>
        <p>{book.get('description','No description available.')}</p>
    </div>
    """
    return html

def toggle_card(current_html, book_id):
    if "card-collapsed" in current_html:
        return expanded_card_html(book_id)
    else:
        book = df[df["id"]==book_id].iloc[0]
        return collapsed_card_html(book['title'], book['authors'])

# ---------- Gradio UI ----------
with gr.Blocks(css="""
.card-collapsed { 
    border:1px solid #444; padding:12px; border-radius:10px; margin:5px; 
    cursor:pointer; transition: all 0.2s; width:220px; text-align:center;
    background:black; color:white; font-weight:bold;
}
.card-collapsed:hover { box-shadow:0 4px 12px rgba(0,0,0,0.3); transform:translateY(-2px);}
.card-expanded { 
    border:1px solid #ccc; padding:12px; border-radius:10px; margin:5px; 
    width:300px; text-align:center; background:white; color:black;
    box-shadow:0 4px 16px rgba(0,0,0,0.2); 
}
.books-container { display:flex; flex-wrap:wrap; max-height:450px; overflow-y:auto; padding:5px; }
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

    # ---------- JS to collapse all expanded cards on ESC ----------
    js_escape = """
    <script>
    document.addEventListener('keydown', function(event) {
        if(event.key === 'Escape') {
            let expanded = document.querySelectorAll('.card-expanded');
            expanded.forEach(card => {
                const title = card.getAttribute('data-title');
                const authors = card.getAttribute('data-authors');
                card.innerHTML = '<b>' + title + '</b><br><small>' + authors + '</small>';
                card.classList.remove('card-expanded');
                card.classList.add('card-collapsed');
            });
        }
    });
    </script>
    """
    gr.HTML(js_escape)

demo.launch()
