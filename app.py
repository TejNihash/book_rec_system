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
        <div class='card-collapsed' 
             data-id='{book['id']}' 
             data-title="{book['title']}" 
             data-authors="{', '.join(book['authors'])}" 
             data-genres="{', '.join(book['genres'])}" 
             data-img="{book['image_url']}" 
             data-desc="{book.get('description', 'No description available.')}">
            <img src="{book['image_url']}" 
                 onerror="this.src='https://via.placeholder.com/120x180/667eea/white?text=No+Image'"
                 style="width:100%;height:150px;object-fit:cover;border-radius:6px;margin-bottom:6px;">
            <b>{book['title']}</b><br>
            <small>{', '.join(book['authors'])}</small>
        </div>
        """
        cards.append(card)
    return f"<div class='books-container'>{''.join(cards)}</div>"

# ---------- Gradio UI ----------
with gr.Blocks(css="""
.books-container {
    display:flex; flex-wrap:nowrap; overflow-x:auto; gap:10px; padding:10px;
}
.card-collapsed { 
    border:1px solid #444; padding:12px; border-radius:10px; margin:5px; 
    cursor:pointer; transition: all 0.2s; width:200px; text-align:center;
    background:black; color:white; font-weight:bold; flex:0 0 auto;
}
.card-collapsed:hover { box-shadow:0 4px 12px rgba(0,0,0,0.3); transform:translateY(-2px);}
.card-expanded { 
    border:1px solid #ccc; padding:16px; border-radius:10px; margin:5px; 
    width:500px; text-align:left; background:white; color:black;
    box-shadow:0 4px 16px rgba(0,0,0,0.2);
    flex:0 0 90%;
}
.books-container::-webkit-scrollbar { height:8px; }
.books-container::-webkit-scrollbar-thumb { background:#bbb; border-radius:4px; }
""") as demo:

    gr.Markdown("# 📚 Interactive Book Cards (Horizontal Scroll + Expand/Collapse + ESC)")

    start_idx = gr.State(0)
    books_html = gr.HTML(value=make_books_html(0, BOOKS_PER_LOAD))

    def load_more_books(start_idx):
        start_idx += BOOKS_PER_LOAD
        new_html = make_books_html(start_idx, BOOKS_PER_LOAD)
        return new_html, start_idx

    load_more_btn = gr.Button("📚 Load More Books")
    load_more_btn.click(load_more_books, inputs=[start_idx], outputs=[books_html, start_idx])

    # ---------- JS Interactivity ----------
    gr.HTML("""
    <script>
    function collapseCard(card, img, title, authors) {
        card.outerHTML = `
            <div class='card-collapsed' 
                 data-title="${title}" data-authors="${authors}" data-img="${img}">
                <img src="${img}" 
                     style="width:100%;height:150px;object-fit:cover;border-radius:6px;margin-bottom:6px;">
                <b>${title}</b><br><small>${authors}</small>
            </div>`;
    }

    document.addEventListener('click', function(e) {
        const card = e.target.closest('.card-collapsed, .card-expanded');
        if (!card) return;

        if (card.classList.contains('card-collapsed')) {
            const img = card.dataset.img;
            const title = card.dataset.title;
            const authors = card.dataset.authors;
            const genres = card.dataset.genres;
            const desc = card.dataset.desc;
            card.outerHTML = `
                <div class='card-expanded' 
                     data-title="${title}" data-authors="${authors}" data-img="${img}">
                    <div style="display:flex;gap:20px;">
                        <img src="${img}" 
                             style="width:180px;height:auto;border-radius:6px;">
                        <div>
                            <h2>${title}</h2>
                            <p><strong>Author(s):</strong> ${authors}</p>
                            <p><strong>Genres:</strong> ${genres}</p>
                            <div style="margin-top:10px;">${desc}</div>
                        </div>
                    </div>
                </div>`;
        }
    });

    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            document.querySelectorAll('.card-expanded').forEach(card => {
                const title = card.dataset.title;
                const authors = card.dataset.authors;
                const img = card.dataset.img;
                collapseCard(card, img, title, authors);
            });
        }
    });
    </script>
    """)

demo.launch()
