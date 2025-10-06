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
                 onerror="this.src='https://via.placeholder.com/120x180/667eea/white?text=No+Image'"
                 class='book-cover'>
            <div class='book-title'>{book['title']}</div>
            <div class='book-authors'>{', '.join(book['authors'])}</div>
        </div>
        """
        cards.append(card)
    return f"<div class='books-container'>{''.join(cards)}</div>"

# ---------- Gradio UI ----------
with gr.Blocks(css="""
.books-container {
    display:flex; flex-wrap:nowrap; overflow-x:auto; gap:15px; padding:10px;
}
.book-card { 
    border:1px solid #444; padding:10px; border-radius:10px; 
    cursor:pointer; transition: all 0.2s; width:180px; text-align:center;
    background:black; color:white; font-weight:bold; flex:0 0 auto;
}
.book-card:hover { box-shadow:0 4px 12px rgba(0,0,0,0.3); transform:translateY(-2px);}
.book-cover { 
    width:100%; height:150px; object-fit:cover; border-radius:6px; margin-bottom:8px;
}
.book-title { font-size:13px; font-weight:bold; }
.book-authors { font-size:11px; color:#ccc; }

.books-container::-webkit-scrollbar { height:8px; }
.books-container::-webkit-scrollbar-thumb { background:#bbb; border-radius:4px; }

#detail-overlay {
    position:fixed; top:0; left:0; width:100%; height:100%;
    background:rgba(0,0,0,0.6); display:none; justify-content:center; align-items:center;
    z-index:999;
}
#detail-box {
    background:white; color:black; padding:25px; border-radius:12px;
    width:700px; max-height:80vh; overflow-y:auto; box-shadow:0 4px 16px rgba(0,0,0,0.3);
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

    gr.Markdown("# 📚 Book Explorer — Horizontal Scroll with Overlay Details")

    start_idx = gr.State(0)
    books_html = gr.HTML(value=make_books_html(0, BOOKS_PER_LOAD))

    def load_more_books(start_idx):
        start_idx += BOOKS_PER_LOAD
        new_html = make_books_html(start_idx, BOOKS_PER_LOAD)
        return new_html, start_idx

    load_more_btn = gr.Button("📚 Load More Books")
    load_more_btn.click(load_more_books, inputs=[start_idx], outputs=[books_html, start_idx])

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
            <div style="display:flex;gap:20px;">
                <img src="${img}" style="width:200px;height:auto;border-radius:8px;">
                <div>
                    <h2 style="margin:0;">${title}</h2>
                    <p><strong>Author(s):</strong> ${authors}</p>
                    <p><strong>Genres:</strong> ${genres}</p>
                    <div style="margin-top:10px; line-height:1.5;">${desc}</div>
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
