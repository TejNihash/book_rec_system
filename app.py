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

# ---------- Helpers ----------
def create_book_card_html(book, is_fav=False):
    fav_text = "Remove from Favorites" if is_fav else "Add to Favorites"
    return f"""
    <div class='book-card' 
         data-id='{book["id"]}' 
         data-title="{book['title']}" 
         data-authors="{', '.join(book['authors'])}" 
         data-genres="{', '.join(book['genres'])}" 
         data-img="{book['image_url']}" 
         data-desc="{book.get('description','No description available.')}">
        <img src="{book['image_url']}" onerror="this.src='https://via.placeholder.com/150x220/667eea/white?text=No+Image'">
        <div class='book-title'>{book['title']}</div>
        <div class='book-authors'>by {', '.join(book['authors'])}</div>
        <button class='fav-btn' data-id='{book["id"]}'>{fav_text}</button>
    </div>
    """

def build_books_grid_html(books_df, favorites):
    if books_df.empty:
        return "<div class='no-books'>No books found</div>"
    cards_html = [
        create_book_card_html(book, is_fav=book["id"] in favorites)
        for _, book in books_df.iterrows()
    ]
    return f"<div class='books-grid'>{''.join(cards_html)}</div>"

def build_favorites_sidebar(favorites):
    if not favorites:
        return "<div class='sidebar-empty'>No favorites added yet.</div>"
    fav_books = df[df["id"].isin(favorites)]
    fav_html = "".join(
        f"<div class='fav-item'><strong>{row['title']}</strong><br><small>by {', '.join(row['authors'][:2])}</small></div>"
        for _, row in fav_books.iterrows()
    )
    return f"<div class='fav-sidebar'>{fav_html}</div>"

# ---------- UI ----------
with gr.Blocks(css="""
.books-grid { display:grid; grid-template-columns: repeat(6,1fr); gap:12px; }
.book-card { background:#fff; border-radius:8px; padding:6px; box-shadow:0 2px 6px rgba(0,0,0,0.15);
            cursor:pointer; text-align:center; transition:all 0.2s ease; position:relative; }
.book-card:hover { transform:translateY(-2px); box-shadow:0 4px 12px rgba(0,0,0,0.25); }
.book-card img { width:100%; height:160px; object-fit:cover; border-radius:4px; margin-bottom:6px; }
.book-title { font-size:12px; font-weight:bold; color:#222; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; }
.book-authors { font-size:10px; color:#555; margin-bottom:6px; }
.fav-btn { background:#667eea; color:white; border:none; border-radius:6px; padding:4px 8px; font-size:10px; cursor:pointer; }
.fav-btn:hover { background:#5563d9; }
.sidebar {
    position: sticky;
    top: 10px;            /* distance from the top of the screen */
    align-self: flex-start;
    background: #f7f7f7;
    border-left: 1px solid #ccc;
    padding: 12px;
    min-width: 220px;
    max-width: 250px;
    height: fit-content;
    overflow-y: auto;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.fav-item { background:#fff; border-radius:6px; padding:8px; margin-bottom:8px; box-shadow:0 2px 6px rgba(0,0,0,0.1); font-size:12px; color:#222; }
#detail-overlay { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.7); z-index:1000; }
#detail-box { position:absolute; background:#fff; border-radius:8px; padding:16px; max-width:600px; box-shadow:0 8px 20px rgba(0,0,0,0.35); color:#111; }
#detail-close { position:absolute; top:8px; right:12px; cursor:pointer; font-size:20px; font-weight:bold; }
""") as demo:

    gr.Markdown("# 📚 Book Explorer")
    gr.Markdown("Click a card to see details, or use **Add to Favorites** to manage your list.")

    favorites_state = gr.State([])

    with gr.Row():
        with gr.Column(scale=5):
            gr.Markdown("### 🎲 Random Books")
            random_loaded_state = gr.State(df.sample(frac=1).reset_index(drop=True))
            random_display_state = gr.State(pd.DataFrame())
            random_page_state = gr.State(0)
            random_container = gr.HTML()
            random_load_btn = gr.Button("📚 Load More Random Books")

            gr.Markdown("### 📈 Popular Books")
            popular_loaded_state = gr.State(df.head(len(df)))
            popular_display_state = gr.State(pd.DataFrame())
            popular_page_state = gr.State(0)
            popular_container = gr.HTML()
            popular_load_btn = gr.Button("📚 Load More Popular Books")

        with gr.Column(scale=1, elem_classes=["sidebar"]):
            gr.Markdown("### ❤️ Favorites")
            favorites_box = gr.HTML(build_favorites_sidebar([]))

    # ---------- Python logic ----------
    def load_more(loaded_books, display_books, page_idx, favorites):
        start = page_idx * BOOKS_PER_LOAD
        end = start + BOOKS_PER_LOAD
        new_books = loaded_books.iloc[start:end]
        if new_books.empty:
            return display_books, gr.update(visible=False), page_idx
        combined = pd.concat([display_books, new_books], ignore_index=True)
        html = build_books_grid_html(combined, favorites)
        return combined, gr.update(value=html), page_idx + 1

    random_load_btn.click(
        load_more,
        [random_loaded_state, random_display_state, random_page_state, favorites_state],
        [random_display_state, random_container, random_page_state],
    )
    popular_load_btn.click(
        load_more,
        [popular_loaded_state, popular_display_state, popular_page_state, favorites_state],
        [popular_display_state, popular_container, popular_page_state],
    )

    # Initial load
    def initial_load(loaded_books, favorites):
        return load_more(loaded_books, pd.DataFrame(), 0, favorites)

    random_display_state.value, random_container.value, random_page_state.value = initial_load(random_loaded_state.value, [])
    popular_display_state.value, popular_container.value, popular_page_state.value = initial_load(popular_loaded_state.value, [])

    # Toggle favorites
    def toggle_favorite(book_id, favorites):
        if book_id in favorites:
            favorites.remove(book_id)
        else:
            favorites.append(book_id)
        return favorites, build_favorites_sidebar(favorites), build_books_grid_html(df.head(BOOKS_PER_LOAD), favorites)

    fav_hidden_input = gr.Textbox(visible=False)
    fav_toggle_btn = gr.Button("hidden", visible=False)

    fav_toggle_btn.click(
        toggle_favorite,
        [fav_hidden_input, favorites_state],
        [favorites_state, favorites_box, random_container],
    )

    # ---------- JS for click handling ----------
    gr.HTML("""
<div id="detail-overlay">
  <div id="detail-box">
    <span id="detail-close">&times;</span>
    <div id="detail-content"></div>
  </div>
</div>
<script>
const overlay = document.getElementById('detail-overlay');
const box = document.getElementById('detail-box');
const closeBtn = document.getElementById('detail-close');
function escapeHtml(str){return str?String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;'):"";}

document.addEventListener('click', e=>{
    // Favorites button
    const favBtn = e.target.closest('.fav-btn');
    if(favBtn){
        const id = favBtn.dataset.id;
        const hiddenInput = document.querySelector('input[type="text"]');
        const hiddenBtn = document.querySelector('button[aria-label="hidden"]');
        if(hiddenInput && hiddenBtn){
            hiddenInput.value = id;
            hiddenBtn.click();
        }
        e.stopPropagation();
        return;
    }

    // Card details
    const card = e.target.closest('.book-card'); 
    if(!card) return;
    const title = card.dataset.title;
    const authors = card.dataset.authors;
    const genres = card.dataset.genres;
    const desc = card.dataset.desc;
    const img = card.dataset.img;
    document.getElementById('detail-content').innerHTML = `
        <div style="display:flex;gap:16px;align-items:flex-start;">
            <img src="${img}" style="width:220px;height:auto;border-radius:6px;object-fit:cover;">
            <div style="max-width:340px;">
                <h2 style="margin:0 0 8px 0; color:#222;">${escapeHtml(title)}</h2>
                <p><strong>Author(s):</strong> ${escapeHtml(authors)}</p>
                <p><strong>Genres:</strong> ${escapeHtml(genres)}</p>
                <div style="margin-top:6px;">${escapeHtml(desc)}</div>
            </div>
        </div>`;
    const rect = card.getBoundingClientRect();
    box.style.left = Math.min(rect.left, window.innerWidth - box.offsetWidth - 10) + 'px';
    box.style.top = Math.min(rect.top, window.innerHeight - box.offsetHeight - 10) + 'px';
    overlay.style.display = 'block';
});
closeBtn.addEventListener('click', ()=>{overlay.style.display='none';});
overlay.addEventListener('click', e=>{if(e.target===overlay) overlay.style.display='none';});
document.addEventListener('keydown', e=>{if(e.key==='Escape') overlay.style.display='none';});
</script>
""")

demo.launch()
