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
def collapsed_card_html(book):
    """Collapsed card with cover thumbnail"""
    return f"""
    <div class='card-collapsed' data-id="{book['id']}" data-title="{book['title']}" data-authors="{', '.join(book['authors'])}">
        <img src="{book['image_url']}" style="width:100%;height:120px;object-fit:cover;border-radius:6px;margin-bottom:6px;" 
             onerror="this.src='https://via.placeholder.com/120x180/667eea/white?text=No+Image'">
        <b>{book['title']}</b><br><small>{', '.join(book['authors'])}</small>
    </div>
    """

def expanded_card_html(book_id):
    """Bigger detail view"""
    book = df[df["id"] == book_id].iloc[0]
    html = f"""
    <div class='card-expanded' data-id="{book['id']}" data-title="{book['title']}" data-authors="{', '.join(book['authors'])}">
        <div style="display:flex; gap:20px; align-items:flex-start;">
            <img src="{book['image_url']}" style="width:180px;height:auto;border-radius:6px;" 
                 onerror="this.src='https://via.placeholder.com/180x270/667eea/white?text=No+Image'">
            <div>
                <h2 style="margin:0 0 10px 0;color:#2c3e50;">{book['title']}</h2>
                <p style="margin:4px 0;color:#666;"><strong>Author(s):</strong> {', '.join(book['authors'])}</p>
                <p style="margin:4px 0;color:#666;"><strong>Genres:</strong> {', '.join(book['genres'])}</p>
                <p style="margin:4px 0;color:#666;"><strong>Published:</strong> {book.get('published_year','Unknown')}</p>
                <p style="margin:4px 0;color:#666;"><strong>Rating:</strong> {book.get('average_rating','Not rated')}</p>
                <div style="margin-top:10px;line-height:1.5;color:#555;">
                    {book.get('description','No description available.')}
                </div>
            </div>
        </div>
    </div>
    """
    return html

def toggle_card(current_html, book_id):
    """Switch between collapsed and expanded view"""
    if "card-collapsed" in current_html:
        return expanded_card_html(book_id)
    else:
        book = df[df["id"]==book_id].iloc[0]
        return collapsed_card_html(book)

def make_books_html(start, count):
    """Return all cards as HTML grid"""
    subset = df.sample(frac=1).reset_index(drop=True).iloc[start:start+count]
    cards_html = "".join(collapsed_card_html(book) for _, book in subset.iterrows())
    return f"<div class='books-container'>{cards_html}</div>"

# ---------- Gradio UI ----------
with gr.Blocks(css="""
.card-collapsed { 
    border:1px solid #444; padding:12px; border-radius:10px; margin:5px; 
    cursor:pointer; transition: all 0.2s; width:220px; text-align:center;
    background:black; color:white; font-weight:bold;
    flex:0 0 auto;
}
.card-collapsed:hover { box-shadow:0 4px 12px rgba(0,0,0,0.3); transform:translateY(-2px);}
.card-expanded { 
    border:1px solid #ccc; padding:12px; border-radius:10px; margin:5px; 
    width:500px; text-align:left; background:white; color:black;
    box-shadow:0 4px 16px rgba(0,0,0,0.2); 
    flex:1 1 100%;
}
.books-container { display:flex; flex-wrap:nowrap; overflow-x:auto; gap:10px; padding:5px; }
.books-container::-webkit-scrollbar { height:8px; }
.books-container::-webkit-scrollbar-thumb { background:#bbb; border-radius:4px; }
""") as demo:

    gr.Markdown("# 📚 Horizontal Book Cards + ESC Collapse")

    start_idx = gr.State(0)
    books_html = gr.HTML(value=make_books_html(0, BOOKS_PER_LOAD))

    def load_more_books(start_idx):
        start_idx += BOOKS_PER_LOAD
        new_html = make_books_html(start_idx, BOOKS_PER_LOAD)
        return new_html, start_idx

    load_more_btn = gr.Button("📚 Load More Books")
    load_more_btn.click(fn=load_more_books, inputs=[start_idx], outputs=[books_html, start_idx])

    # ESC collapse JS
    gr.HTML("""
    <script>
    document.addEventListener('keydown', function(event) {
        if(event.key === 'Escape') {
            document.querySelectorAll('.card-expanded').forEach(card => {
                const title = card.getAttribute('data-title');
                const authors = card.getAttribute('data-authors');
                const img = card.querySelector('img')?.src || '';
                card.outerHTML = `
                    <div class='card-collapsed' data-title="${title}" data-authors="${authors}">
                        <img src="${img}" style="width:100%;height:120px;object-fit:cover;border-radius:6px;margin-bottom:6px;">
                        <b>${title}</b><br><small>${authors}</small>
                    </div>
                `;
            });
        }
    });
    </script>
    """)

demo.launch()
