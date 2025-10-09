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
        <img src="{book['image_url']}" onerror="this.src='https://via.placeholder.com/120x180/667eea/white?text=No+Image'">
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
.app-container { 
    display:flex; 
    height:100vh; 
    overflow:hidden; 
    font-family: 'Inter', 'Segoe UI', sans-serif; 
    background: #0e0e10;
    color: #e6e6e6;
}

/* ---------- Main Content ---------- */
.main-content { 
    flex-grow:1; 
    overflow-y:auto; 
    padding:16px; 
    max-width:calc(100% - 320px); 
}
.main-content h1, .main-content h2, .main-content h3 {
    color: #ffffff;
}

/* ---------- Sidebar ---------- */
.sidebar { 
    width:300px; 
    background:#141416; 
    border-left:1px solid #2a2a2a; 
    padding:16px; 
    box-sizing:border-box;
    overflow-y:auto; 
    position:fixed; 
    right:0; top:0; bottom:0;
}
.sidebar h2 {
    color: #ffffff;
}
.sidebar p, .sidebar div {
    color: #ccc;
}

/* ---------- Books Grid ---------- */
.books-grid { 
    display:grid; 
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); 
    gap:16px; 
}

/* ---------- Book Cards ---------- */
.book-card { 
    background:#1b1b1e; 
    border-radius:8px; 
    padding:8px; 
    box-shadow:0 0 10px rgba(255,255,255,0.05); 
    cursor:pointer; 
    text-align:center; 
    transition: all 0.25s ease; 
    position:relative;
    border: 1px solid #2d2d2d;
}
.book-card:hover { 
    transform:translateY(-4px); 
    box-shadow:0 0 18px rgba(120, 180, 255, 0.3);
}

/* ---------- Book Image ---------- */
.book-card img { 
    width:100%; 
    height:180px; 
    object-fit:cover; 
    border-radius:6px; 
    margin-bottom:8px; 
}

/* ---------- Text Styling ---------- */
.book-title { 
    font-size:13px; 
    font-weight:600; 
    color:#f3f3f3; 
    overflow:hidden; 
    display:-webkit-box; 
    -webkit-line-clamp:2; 
    -webkit-box-orient:vertical;
}
.book-authors { 
    font-size:11px; 
    color:#9ba1b0; 
    overflow:hidden; 
    display:-webkit-box; 
    -webkit-line-clamp:1; 
    -webkit-box-orient:vertical;
}

/* ---------- Buttons ---------- */
.fav-btn { 
    font-size:11px; 
    margin-top:6px; 
    padding:4px 8px; 
    border:none; 
    border-radius:4px; 
    cursor:pointer; 
    background:linear-gradient(90deg,#3a3f47,#4f5460); 
    color:#fff; 
    transition: all 0.2s ease;
}
.fav-btn:hover { 
    background:linear-gradient(90deg,#5a60ff,#3b8dff);
}
.fav-btn.fav-active { 
    background:linear-gradient(90deg,#ffb800,#ff8800);
    color:#000;
}

/* ---------- No Books ---------- */
.no-books {
    text-align:center;
    color:#888;
    margin-top:20px;
}

/* ---------- Overlay ---------- */
#detail-overlay { 
    display:none; 
    position:fixed; 
    top:0; left:0; 
    width:100%; height:100%; 
    background:rgba(0,0,0,0.8); 
    z-index:1000;
    backdrop-filter: blur(6px);
}

/* ---------- Popup Box ---------- */
#detail-box { 
    position:absolute; 
    background:#1b1b1e; 
    border-radius:10px; 
    padding:20px; 
    max-width:520px; 
    box-shadow:0 8px 25px rgba(0,0,0,0.6); 
    color:#e6e6e6;
    border: 1px solid #2a2a2a;
}
#detail-close { 
    position:absolute; 
    top:8px; right:12px; 
    cursor:pointer; 
    font-size:20px; 
    font-weight:bold; 
    color:#888;
}
#detail-close:hover { 
    color:#fff; 
}

/* ---------- Detail Text ---------- */
#detail-content { 
    line-height:1.5; 
    font-size:14px; 
    color:#ddd;
}

/* ---------- Scrollbar ---------- */
::-webkit-scrollbar {
    width: 8px;
}
::-webkit-scrollbar-thumb {
    background: #3a3a3a;
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: #555;
}
""") as demo:

    with gr.Row(elem_classes="app-container"):
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
    return str ? String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;')
                     .replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;') : "";
}

function updateFavoritesSidebar(){
    const sidebarContent = document.querySelector('.sidebar > div');
    if(!sidebarContent) return;
    if(favorites.size===0){
        sidebarContent.innerHTML = "<p>No favorites yet.</p>";
        return;
    }
    let html = "";
    favorites.forEach((book,id)=>{
        html += `<div class="sidebar-book" data-id="${id}">
            <img src="${escapeHtml(book.img)}" style="width:36px;height:52px;object-fit:cover;border-radius:4px;margin-right:6px;">
            <div style="font-size:12px;"><strong>${escapeHtml(book.title)}</strong><br>${escapeHtml(book.authors)}</div>
        </div>`;
    });
    sidebarContent.innerHTML = html;
}

document.addEventListener('click', e=>{
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
        }else{
            favorites.set(bookId,{title,authors,img});
            favBtn.classList.add('fav-active');
        }
        updateFavoritesSidebar();
        return;
    }

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
            <div style="max-width:240px;">
                <h2 style="margin:0 0 8px 0;color:#222;">${escapeHtml(title)}</h2>
                <p style="margin:0 0 4px 0;color:#222;"><strong>Author(s):</strong> ${escapeHtml(authors)}</p>
                <p style="margin:0 0 6px 0;color:#222;"><strong>Genres:</strong> ${escapeHtml(genres)}</p>
                <div style="margin-top:6px;color:#222;">${escapeHtml(desc)}</div>
            </div>
        </div>
    `;

    const rect = card.getBoundingClientRect();
    let left = rect.right + 10;
    let top = rect.top;

    // Adjust horizontal overflow
    if (left + box.offsetWidth > window.innerWidth - 20) {
        left = rect.left - box.offsetWidth - 10;
    }

    // Adjust vertical overflow
    if (top + box.offsetHeight > window.innerHeight - 20) {
        top = window.innerHeight - box.offsetHeight - 20;
    }

    box.style.left = `${Math.max(left, 10)}px`;
    box.style.top = `${Math.max(top, 10)}px`;

    overlay.style.display='block';
    box.scrollIntoView({ behavior: "smooth", block: "nearest" });
});

closeBtn.addEventListener('click',()=>{overlay.style.display='none';});
overlay.addEventListener('click',e=>{if(e.target===overlay) overlay.style.display='none';});
document.addEventListener('keydown',e=>{if(e.key==='Escape') overlay.style.display='none';});
</script>
""")

demo.launch()
