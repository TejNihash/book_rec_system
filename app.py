import ast
import pandas as pd
import gradio as gr

# ---------- Load dataset ----------
df = pd.read_csv("data_mini_books.csv")
if "id" not in df.columns:
    df["id"] = df.index.astype(str)
df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

BOOKS_PER_LOAD = 12  # 2 rows × 6 columns

# ---------- Helpers ----------
def create_book_card_html(book):
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
        <button class='fav-btn' title='Add to Favorites'>&#9734;</button>
    </div>
    """

def build_books_grid_html(books_df):
    if books_df.empty:
        return "<div class='no-books'>No books found</div>"
    cards_html = [create_book_card_html(book) for _, book in books_df.iterrows()]
    return f"<div class='books-grid'>{''.join(cards_html)}</div>"

# ---------- Gradio UI ----------
with gr.Blocks(css="""
  body {
    margin: 0;
    font-family: Arial, sans-serif;
  }
  .app-container {
    display: flex;
    height: 100vh;
    overflow: hidden;
  }
  .main-content {
    flex-grow: 1;
    overflow-y: auto;
    padding: 12px 20px 12px 12px;
    max-width: calc(100% - 300px);
  }
  .sidebar {
    width: 300px;
    background: #f0f2f5;
    border-left: 1px solid #ddd;
    padding: 12px;
    box-sizing: border-box;
    overflow-y: auto;
    position: fixed;
    right: 0;
    top: 0;
    bottom: 0;
  }
  .sidebar h3 {
    margin-top: 0;
    font-weight: bold;
    color: #333;
  }
  .sidebar-book {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    font-size: 14px;
  }
  .sidebar-book img {
    width: 36px;
    height: 52px;
    object-fit: cover;
    border-radius: 4px;
    border: 1px solid #ccc;
  }
  .sidebar-book-title {
    font-weight: 600;
    color: #222;
  }
  .books-section { border:1px solid #e0e0e0; border-radius:12px; padding:12px; 
                   max-height:500px; overflow-y:auto; margin-bottom:10px; background:#f7f7f7;}
  .books-grid { display:grid; grid-template-columns: repeat(6,1fr); gap:12px; }
  .book-card { background:#fff; border-radius:8px; padding:6px; box-shadow:0 2px 6px rgba(0,0,0,0.15);
              cursor:pointer; text-align:center; transition:all 0.2s ease; position:relative; }
  .book-card:hover { transform:translateY(-2px); box-shadow:0 4px 12px rgba(0,0,0,0.25); }
  .book-card img { width:100%; height:160px; object-fit:cover; border-radius:4px; margin-bottom:6px; }
  .book-title { font-size:12px; font-weight:bold; color:#222; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; }
  .book-authors { font-size:10px; color:#555; overflow:hidden; display:-webkit-box; -webkit-line-clamp:1; -webkit-box-orient:vertical; }
  .fav-btn {
    background: transparent;
    border: none;
    cursor: pointer;
    font-size: 18px;
    color: #999;
    margin-top: 4px;
    transition: color 0.3s ease;
  }
  .fav-btn.fav-active {
    color: #ffcc00;  /* gold star for active favorite */
  }
  .fav-btn:hover {
    color: #ffcc00;
  }
  #detail-overlay { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.7); z-index:1000; }
  #detail-box { position:absolute; background:#fff; border-radius:8px; padding:16px; max-width:600px; box-shadow:0 8px 20px rgba(0,0,0,0.35); color:#111; }
  #detail-close { position:absolute; top:8px; right:12px; cursor:pointer; font-size:20px; font-weight:bold; }
  #detail-content { line-height:1.5; font-size:14px; color:#111; }
""") as demo:

    gr.HTML('<div class="app-container">')  # Opening wrapper div

    with gr.Column(elem_classes="main-content"):
        gr.Markdown("# 🎲 Random & Popular Books")

        # ---------- Random Books ----------
        gr.Markdown("🎲 Random Books")
        random_loaded_state = gr.State(df.sample(frac=1).reset_index(drop=True))
        random_display_state = gr.State(pd.DataFrame())
        random_page_state = gr.State(0)
        random_container = gr.HTML()
        random_load_btn = gr.Button("📚 Load More Random Books")

        # ---------- Popular Books ----------
        gr.Markdown("📚 Popular Books")
        popular_loaded_state = gr.State(df.head(len(df)))
        popular_display_state = gr.State(pd.DataFrame())
        popular_page_state = gr.State(0)
        popular_container = gr.HTML()
        popular_load_btn = gr.Button("📚 Load More Popular Books")

        # ---------- Load more logic ----------
        def load_more(loaded_books, display_books, page_idx):
            start = page_idx * BOOKS_PER_LOAD
            end = start + BOOKS_PER_LOAD
            new_books = loaded_books.iloc[start:end]
            if new_books.empty:
                return display_books, gr.update(visible=False), page_idx
            combined = pd.concat([display_books, new_books], ignore_index=True)
            html = build_books_grid_html(combined)
            return combined, gr.update(value=html), page_idx + 1

        random_load_btn.click(
            load_more,
            [random_loaded_state, random_display_state, random_page_state],
            [random_display_state, random_container, random_page_state]
        )
        popular_load_btn.click(
            load_more,
            [popular_loaded_state, popular_display_state, popular_page_state],
            [popular_display_state, popular_container, popular_page_state]
        )

        # ---------- Initial load ----------
        def initial_load(loaded_books):
            return load_more(loaded_books, pd.DataFrame(), 0)

        random_display_state.value, random_container.value, random_page_state.value = initial_load(random_loaded_state.value)
        popular_display_state.value, popular_container.value, popular_page_state.value = initial_load(popular_loaded_state.value)

    with gr.Column(elem_classes="sidebar"):
        gr.Markdown("## ⭐ Favorites")
        favorites_container = gr.HTML("<p>No favorites yet.</p>")

    gr.HTML('</div>')  # Closing wrapper div

    # ---------- Detail popup + Favorite button JS + Sidebar update JS ----------
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
const favorites = new Map();  // key: bookId, value: {title, authors, img}

function escapeHtml(str){
    return str ? String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
              .replace(/"/g,'&quot;').replace(/'/g,'&#39;') : "";
}

function updateFavoritesSidebar() {
    const sidebarContent = document.querySelector('.sidebar > div');
    if (!sidebarContent) return;
    if (favorites.size === 0) {
        sidebarContent.innerHTML = "<p>No favorites yet.</p>";
        return;
    }
    let html = "";
    favorites.forEach((book, id) => {
        html += `
        <div class="sidebar-book" data-id="${id}">
            <img src="${escapeHtml(book.img)}" alt="${escapeHtml(book.title)}" />
            <div>
                <div class="sidebar-book-title">${escapeHtml(book.title)}</div>
                <div style="font-size:12px; color:#666;">by ${escapeHtml(book.authors)}</div>
            </div>
        </div>
        `;
    });
    sidebarContent.innerHTML = html;
}

document.addEventListener('click', e => {
    const favBtn = e.target.closest('.fav-btn');
    if (favBtn) {
        e.stopPropagation();
        const card = favBtn.closest('.book-card');
        const bookId = card.dataset.id;
        const title = card.dataset.title;
        const authors = card.dataset.authors;
        const img = card.dataset.img;
        if (favorites.has(bookId)) {
            favorites.delete(bookId);
            favBtn.classList.remove('fav-active');
            favBtn.title = 'Add to Favorites';
            favBtn.innerHTML = '&#9734;';
        } else {
            favorites.set(bookId, {title:title, authors:authors, img:img});
            favBtn.classList.add('fav-active');
            favBtn.title = 'Remove from Favorites';
            favBtn.innerHTML = '&#9733;';
        }
        updateFavoritesSidebar();
        return;
    }

    const card = e.target.closest('.book-card'); 
    if (!card) return;
    const title = card.dataset.title;
    const authors = card.dataset.authors;
    const genres = card.dataset.genres;
    const desc = card.dataset.desc;
    const img = card.dataset.img;
    document.getElementById('detail-content').innerHTML = `
        <div style="display:flex;gap:16px;align-items:flex-start;">
            <img src="${img}" style="width:220px;height:auto;border-radius:6px;object-fit:cover;">
            <div style="max-width:340px;">
                <h2 style="margin:0 0 8px 0; color:#222222;">${escapeHtml(title)}</h2>
                <p style="margin:0 0 4px 0; color:#222222;"><strong>Author(s):</strong> ${escapeHtml(authors)}</p>
                <p style="margin:0 0 6px 0; color:#222222;"><strong>Genres:</strong> ${escapeHtml(genres)}</p>
                <div style="margin-top:6px; color:#222222;">${escapeHtml(desc)}</div>
            </div>
        </div>
    `;
    const rect = card.getBoundingClientRect();
    box.style.left = Math.min(rect.left, window.innerWidth - box.offsetWidth - 10) + 'px';
    box.style.top = Math.min(rect.top, window.innerHeight - box.offsetHeight - 10) + 'px';
    overlay.style.display = 'block';
});

closeBtn.addEventListener('click', () => { overlay.style.display='none'; });
overlay.addEventListener('click', e => { if(e.target===overlay) overlay.style.display='none'; });
document.addEventListener('keydown', e => { if(e.key==='Escape') overlay.style.display='none'; });
</script>
""")

demo.launch()
