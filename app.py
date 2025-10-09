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
def create_book_card_html(book):
    return f"""
    <div class='book-card' 
         data-id='{book["id"]}' 
         data-title="{book['title']}" 
         data-authors="{', '.join(book['authors'])}" 
         data-genres="{', '.join(book['genres'])}" 
         data-img="{book['image_url']}" 
         data-desc="{book.get('description','No description available.')}">
        <img src="{book['image_url']}" 
             onerror="this.src='https://via.placeholder.com/120x180/667eea/white?text=No+Image'">
        <div class='book-title'>{book['title']}</div>
        <div class='book-authors'>by {', '.join(book['authors'])}</div>
        <button class='fav-btn' title='Add to Favorites'>Add to Fav</button>
    </div>
    """

def build_books_grid_html(books_df):
    if books_df.empty:
        return "<div class='no-books'>No books found</div>"
    cards_html = [create_book_card_html(book) for _, book in books_df.iterrows()]
    return f"<div class='books-grid'>{''.join(cards_html)}</div>"

# ---------- Gradio UI ----------
with gr.Blocks(css="""
/* ---------- App Layout ---------- */
.app-container { display:flex; height:100vh; overflow:hidden; font-family:'Inter','Segoe UI',sans-serif; background:#0e0e10; color:#eaeaea; }
.main-content { flex-grow:1; overflow-y:auto; padding:16px; max-width:calc(100% - 320px); }
.sidebar { width:300px; background:#141416; border-left:1px solid #2a2a2a; padding:16px; box-sizing:border-box; overflow-y:auto; position:fixed; right:0; top:0; bottom:0; color:#f0f0f0; }

/* ---------- Fixed Scroll Sections ---------- */
.scroll-section { max-height: 500px; overflow-y: auto; border-radius: 8px; padding: 12px; margin-bottom: 20px; background:#1b1b1e; }
.section-header { font-size:20px; font-weight:bold; margin-bottom:12px; color:#fff; border-bottom:2px solid #667eea; padding-bottom:6px; }

/* ---------- Books Grid ---------- */
.books-grid { display:grid; grid-template-columns: repeat(auto-fill,minmax(150px,1fr)); gap:16px; }
.book-card { background:#1b1b1e; border-radius:8px; padding:8px; box-shadow:0 0 10px rgba(255,255,255,0.05); cursor:pointer; text-align:center; transition:all 0.25s ease; position:relative; border:1px solid #2d2d2d; }
.book-card:hover { transform:translateY(-4px); box-shadow:0 0 18px rgba(120,180,255,0.35); }
.book-card img { width:100%; height:180px; object-fit:cover; border-radius:6px; margin-bottom:8px; }
.book-title { font-size:13px; font-weight:600; color:#fff; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; }
.book-authors { font-size:11px; color:#9ba1b0; overflow:hidden; display:-webkit-box; -webkit-line-clamp:1; -webkit-box-orient:vertical; }

/* ---------- Buttons ---------- */
.fav-btn { font-size:11px; margin-top:6px; padding:4px 8px; border:none; border-radius:4px; cursor:pointer; background:linear-gradient(90deg,#3a3f47,#4f5460); color:#fff; transition:all 0.2s ease; }
.fav-btn:hover { background:linear-gradient(90deg,#5a60ff,#3b8dff); }
.fav-btn.fav-active { background:linear-gradient(90deg,#ffb800,#ff8800); color:#000; }
.load-more-btn { width:100%; padding:10px; background:#667eea; color:#fff; border:none; border-radius:6px; cursor:pointer; margin-top:10px; font-weight:bold; }
.load-more-btn:hover { background:#5a6fd8; }
.load-more-btn:disabled { background:#555; cursor:not-allowed; }

/* ---------- Detail Overlay ---------- */
#detail-overlay { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:1000; backdrop-filter:blur(6px); }
#detail-box { position:absolute; background:#1b1b1e; border-radius:10px; padding:20px; max-width:520px; box-shadow:0 8px 25px rgba(0,0,0,0.6); color:#fff; border:1px solid #2a2a2a; }
#detail-close { position:absolute; top:8px; right:12px; cursor:pointer; font-size:20px; font-weight:bold; color:#ccc; }
#detail-close:hover { color:#fff; }
#detail-content { line-height:1.6; font-size:14px; color:#fff; }

/* ---------- Sidebar ---------- */
.sidebar h2 { color:#fff; margin-bottom:12px; }
.sidebar p { color:#999; }
.sidebar-book { display:flex; align-items:center; gap:6px; margin-bottom:10px; }
.sidebar-book:hover { background:#222; border-radius:6px; padding:4px; transition:0.2s; }

/* ---------- Scrollbar ---------- */
.scroll-section::-webkit-scrollbar, .sidebar::-webkit-scrollbar { width:8px; }
.scroll-section::-webkit-scrollbar-thumb, .sidebar::-webkit-scrollbar-thumb { background:#3a3a3a; border-radius:4px; }
.scroll-section::-webkit-scrollbar-thumb:hover, .sidebar::-webkit-scrollbar-thumb:hover { background:#555; }
""") as demo:

    with gr.Row(elem_classes="app-container"):
        with gr.Column(elem_classes="main-content"):
            gr.Markdown("# 📚 Dark Library Explorer")

            # ---------- Random Books Section ----------
            gr.Markdown("🎲 Random Books", elem_classes="section-header")
            random_loaded_state = gr.State(df.sample(frac=1).reset_index(drop=True))
            random_display_state = gr.State(pd.DataFrame())
            random_page_state = gr.State(0)
            
            with gr.Column(elem_classes="scroll-section"):
                random_container = gr.HTML()
            random_load_btn = gr.Button("📘 Load More Random Books", elem_classes="load-more-btn")

            # ---------- Popular Books Section ----------
            gr.Markdown("🌟 Popular Books", elem_classes="section-header")
            popular_loaded_state = gr.State(df.head(len(df)))
            popular_display_state = gr.State(pd.DataFrame())
            popular_page_state = gr.State(0)
            
            with gr.Column(elem_classes="scroll-section"):
                popular_container = gr.HTML()
            popular_load_btn = gr.Button("📖 Load More Popular Books", elem_classes="load-more-btn")

            # ---------- Load more logic ----------
            def load_more(loaded_books, display_books, page_idx):
                start = page_idx * BOOKS_PER_LOAD
                end = start + BOOKS_PER_LOAD
                new_books = loaded_books.iloc[start:end]
                if display_books is None or display_books.empty:
                    display_books = pd.DataFrame()
                if new_books.empty:
                    combined = display_books
                    html = build_books_grid_html(combined)
                    return combined, gr.update(value=html), page_idx, gr.update(visible=False)
                combined = pd.concat([display_books, new_books], ignore_index=True)
                html = build_books_grid_html(combined)
                has_more = end < len(loaded_books)
                return combined, gr.update(value=html), page_idx + 1, gr.update(visible=has_more)

            random_load_btn.click(
                load_more,
                [random_loaded_state, random_display_state, random_page_state],
                [random_display_state, random_container, random_page_state, random_load_btn]
            )
            popular_load_btn.click(
                load_more,
                [popular_loaded_state, popular_display_state, popular_page_state],
                [popular_display_state, popular_container, popular_page_state, popular_load_btn]
            )

            def initial_load(loaded_books):
                return load_more(loaded_books, pd.DataFrame(), 0)

            demo.load(
                lambda: [
                    *initial_load(random_loaded_state.value),
                    *initial_load(popular_loaded_state.value)
                ],
                outputs=[
                    random_display_state, random_container, random_page_state, random_load_btn,
                    popular_display_state, popular_container, popular_page_state, popular_load_btn
                ]
            )

        with gr.Column(elem_classes="sidebar"):
            gr.Markdown("## ⭐ Favorites")
            favorites_container = gr.HTML("<div id='favorites-list'><p>No favorites yet.</p></div>")

    # ---------- Detail popup + Fav JS ----------
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
const favorites = new Map();

function escapeHtml(str){
  return str ? String(str)
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;')
    .replace(/'/g,'&#39;') : "";
}

// ---------- Update Sidebar ----------
function updateFavoritesSidebar(){
  const sidebarList = document.getElementById('favorites-list');
  if(!sidebarList) return;

  if(favorites.size === 0){
    sidebarList.innerHTML = "<p>No favorites yet.</p>";
    return;
  }

  let html = "";
  favorites.forEach((book,id)=>{
    html += `
      <div class="sidebar-book" data-id="${id}">
        <img src="${escapeHtml(book.img)}" 
             style="width:40px;height:56px;object-fit:cover;border-radius:4px;">
        <div style="flex:1;font-size:12px;color:#fff;">
          <strong>${escapeHtml(book.title)}</strong><br>
          <span style="color:#aaa;">${escapeHtml(book.authors)}</span>
        </div>
        <button class="remove-fav-btn" title="Remove from Favorites"
          style="background:none;border:none;color:#888;cursor:pointer;font-size:14px;">
          🗑️
        </button>
      </div>`;
  });
  sidebarList.innerHTML = html;
}

// ---------- Click Handler ----------
document.addEventListener('click', e=>{
  // --- Remove Favorite from Sidebar ---
  if(e.target.closest('.remove-fav-btn')){
    const parent = e.target.closest('.sidebar-book');
    if(!parent) return;
    const id = parent.dataset.id;
    favorites.delete(id);
    updateFavoritesSidebar();
    // also un-highlight the corresponding book card
    const cardBtn = document.querySelector(`.book-card[data-id="${id}"] .fav-btn`);
    if(cardBtn) cardBtn.classList.remove('fav-active');
    return;
  }

  // --- Toggle Favorite from Card ---
  const favBtn = e.target.closest('.fav-btn');
  if(favBtn){
    e.stopPropagation();
    const card = favBtn.closest('.book-card');
    const bookId = card.dataset.id;
    const title = card.dataset.title;
    const authors = card.dataset.authors;
    const img = card.dataset.img;
    if(favorites.has(bookId)){
      favorites.delete(bookId);
      favBtn.classList.remove('fav-active');
    } else {
      favorites.set(bookId,{title,authors,img});
      favBtn.classList.add('fav-active');
    }
    updateFavoritesSidebar();
    return;
  }

  // --- Book Detail Popup ---
  const card = e.target.closest('.book-card');
  if(!card) return;
  const title = card.dataset.title;
  const authors = card.dataset.authors;
  const genres = card.dataset.genres;
  const desc = card.dataset.desc;
  const img = card.dataset.img;

  document.getElementById('detail-content').innerHTML = `
    <div style="display:flex;gap:16px;align-items:flex-start;color:#fff;">
      <img src="${img}" style="width:200px;height:auto;border-radius:6px;object-fit:cover;">
      <div style="max-width:260px;">
        <h2 style="margin:0 0 8px 0;color:#fff;">${escapeHtml(title)}</h2>
        <p style="margin:0 0 4px 0;color:#fff;"><strong>Author(s):</strong> ${escapeHtml(authors)}</p>
        <p style="margin:0 0 6px 0;color:#fff;"><strong>Genres:</strong> ${escapeHtml(genres)}</p>
        <div style="margin-top:6px;color:#fff;">${escapeHtml(desc)}</div>
      </div>
    </div>`;

  const rect = card.getBoundingClientRect();
  let left = rect.right + 10;
  let top = rect.top;
  if(left + box.offsetWidth > window.innerWidth - 20){ left = rect.left - box.offsetWidth - 10; }
  if(top + box.offsetHeight > window.innerHeight - 20){ top = window.innerHeight - box.offsetHeight - 20; }
  box.style.left = `${Math.max(left, 10)}px`;
  box.style.top = `${Math.max(top, 10)}px`;

  overlay.style.display='block';
  box.scrollIntoView({ behavior: "smooth", block: "nearest" });
});

// ---------- Overlay Controls ----------
closeBtn.addEventListener('click',()=>{overlay.style.display='none';});
overlay.addEventListener('click',e=>{if(e.target===overlay) overlay.style.display='none';});
document.addEventListener('keydown',e=>{if(e.key==='Escape') overlay.style.display='none';});
</script>

""")

demo.launch()