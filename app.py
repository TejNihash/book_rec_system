import ast
import pandas as pd
import gradio as gr

# ---------- Load dataset ----------
df = pd.read_csv("data_mini_books.csv")
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

BOOKS_PER_LOAD = 12  # 2 rows of 6

# ---------- HTML rendering ----------
def make_books_html(start, count):
    subset = df.sample(frac=1).reset_index(drop=True).iloc[start:start+count]
    cards = []
    for _, book in subset.iterrows():
        card = f"""
        <div class='book-card' 
             data-id='{book['id']}'
             data-title="{book['title']}" 
             data-authors="{', '.join(book['authors'])}" 
             data-genres="{', '.join(book['genres'])}" 
             data-img="{book['image_url']}" 
             data-desc="{book.get('description', 'No description available.')}">
            <img src="{book['image_url']}" 
                 onerror="this.src='https://via.placeholder.com/120x180/667eea/ffffff?text=No+Image'"
                 class='book-cover'>
            <div class='book-title'>{book['title']}</div>
            <div class='book-authors'>{', '.join(book['authors'])}</div>
        </div>
        """
        cards.append(card)
    return ''.join(cards)

# ---------- Gradio UI ----------
with gr.Blocks(css="""
.books-wrapper {
    max-height: 600px;
    overflow-y: auto;
    background: #121212;
    border-radius: 10px;
    padding: 15px;
    border: 1px solid #333;
}

.books-container {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 15px;
    justify-items: center;
}

.book-card { 
    border:1px solid #444; 
    padding:10px; 
    border-radius:10px; 
    cursor:pointer; 
    transition: all 0.2s; 
    width:160px; 
    text-align:center;
    background:#1e1e1e; 
    color:#f5f5f5; 
    font-weight:bold; 
    flex:0 0 auto;
}
.book-card:hover { box-shadow:0 4px 16px rgba(255,255,255,0.15); transform:translateY(-2px);}
.book-cover { 
    width:100%; height:160px; object-fit:cover; border-radius:6px; margin-bottom:8px;
}
.book-title { font-size:13px; font-weight:bold; color:#fff; }
.book-authors { font-size:11px; color:#bbb; }

.books-wrapper::-webkit-scrollbar { width:8px; }
.books-wrapper::-webkit-scrollbar-thumb { background:#444; border-radius:4px; }

#detail-overlay {
    position:fixed; top:0; left:0; width:100%; height:100%;
    background:rgba(0,0,0,0.6); display:none; justify-content:center; align-items:center;
    z-index:999;
}
#detail-box {
    background:#f8f8f8; color:#111; padding:25px; border-radius:12px;
    width:750px; max-height:80vh; overflow-y:auto; box-shadow:0 4px 16px rgba(0,0,0,0.3);
    animation: fadeIn 0.2s ease-in-out;
}
#detail-close {
    position:absolute; top:15px; right:25px; font-size:22px; font-weight:bold; cursor:pointer;
}
@keyframes fadeIn {
    from { opacity:0; transform:scale(0.95); }
    to { opacity:1; transform:scale(1); }
}
""") as demo:

    gr.Markdown("# 📚 Book Explorer — Scrollable Library with Overlay Details")

    start_idx = gr.State(0)
    all_books_html = gr.HTML(value=f"<div class='books-container'>{make_books_html(0, BOOKS_PER_LOAD)}</div>")

    def load_more_books(current_html, start_idx):
        start_idx += BOOKS_PER_LOAD
        new_cards = make_books_html(start_idx, BOOKS_PER_LOAD)
        combined_html = current_html.replace("</div>", new_cards + "</div>")
        return combined_html, start_idx

    with gr.Column(elem_classes="books-wrapper"):
        all_books_html.render()
        load_more_btn = gr.Button("📖 Load More Books")

    load_more_btn.click(load_more_books, inputs=[all_books_html, start_idx], outputs=[all_books_html, start_idx])

    # ---------- Overlay JS ----------
    gr.HTML("""
    <div id="detail-overlay">
        <div id="detail-box">
            <span id="detail-close">&times;</span>
            <div id="detail-content"></div>
        </div>
    </div>

    <script>
    document.addEventListener('click', function(e) {
        const card = e.target.closest('.book-card');
        if (!card) return;

        const title = card.dataset.title;
        const authors = card.dataset.authors;
        const genres = card.dataset.genres;
        const desc = card.dataset.desc;
        const img = card.dataset.img;

        const detailHTML = `
            <div style="display:flex;gap:20px;align-items:flex-start;">
                <img src="${img}" style="width:220px;height:auto;border-radius:8px;">
                <div>
                    <h2 style="margin:0 0 10px 0;">${title}</h2>
                    <p><strong>Author(s):</strong> ${authors}</p>
                    <p><strong>Genres:</strong> ${genres}</p>
                    <div style="margin-top:10px; line-height:1.6;">${desc}</div>
                </div>
            </div>
        `;

        document.getElementById('detail-content').innerHTML = detailHTML;
        document.getElementById('detail-overlay').style.display = 'flex';
    });

    document.getElementById('detail-close').addEventListener('click', () => {
        document.getElementById('detail-overlay').style.display = 'none';
    });

    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            document.getElementById('detail-overlay').style.display = 'none';
        }
    });
    </script>
    """)

demo.launch()
