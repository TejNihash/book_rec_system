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
        <div class='book-info'>
            <div class='book-title'>{book['title']}</div>
            <div class='book-authors'>by {', '.join(book['authors'])}</div>
        </div>
        <button class='fav-btn' title='Add to Favorites'>❤️</button>
    </div>
    """

def build_books_grid_html(books_df):
    if books_df.empty:
        return "<div class='no-books'>No books found</div>"
    cards_html = [create_book_card_html(book) for _, book in books_df.iterrows()]
    return f"<div class='books-grid'>{''.join(cards_html)}</div>"

# ---------- Gradio UI ----------
with gr.Blocks(css="""
.app-container { 
    display: flex; 
    height: 100vh; 
    overflow: hidden; 
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.main-content { 
    flex-grow: 1; 
    overflow-y: auto; 
    padding: 20px; 
    max-width: calc(100% - 350px);
    background: rgba(255, 255, 255, 0.95);
    margin: 10px;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
}
.sidebar { 
    width: 320px; 
    background: linear-gradient(180deg, #2c3e50 0%, #3498db 100%);
    border-left: 1px solid rgba(255,255,255,0.1); 
    padding: 20px; 
    box-sizing: border-box;
    overflow-y: auto; 
    position: fixed; 
    right: 0; 
    top: 0; 
    bottom: 0; 
    color: white;
}
.section-container {
    background: white;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 25px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    border: 1px solid rgba(0,0,0,0.05);
}
.section-header {
    font-size: 24px;
    font-weight: 700;
    color: #2c3e50;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 2px solid #3498db;
    display: flex;
    align-items: center;
    gap: 10px;
}
.scroll-container {
    max-height: 500px;
    overflow-y: auto;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #e9ecef;
    margin-bottom: 15px;
}
.books-grid { 
    display: grid; 
    grid-template-columns: repeat(6, 1fr); 
    gap: 16px;
    padding: 5px;
}
.book-card { 
    background: white; 
    border-radius: 10px; 
    padding: 12px; 
    box-shadow: 0 3px 15px rgba(0,0,0,0.1);
    cursor: pointer; 
    text-align: center; 
    transition: all 0.3s ease; 
    position: relative;
    border: 1px solid #e9ecef;
    display: flex;
    flex-direction: column;
    height: fit-content;
}
.book-card:hover { 
    transform: translateY(-5px); 
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}
.book-card img { 
    width: 100%; 
    height: 160px; 
    object-fit: cover; 
    border-radius: 6px; 
    margin-bottom: 10px;
    border: 1px solid #e9ecef;
}
.book-info {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.book-title { 
    font-size: 13px; 
    font-weight: 600; 
    color: #2c3e50; 
    overflow: hidden; 
    display: -webkit-box; 
    -webkit-line-clamp: 2; 
    -webkit-box-orient: vertical;
    line-height: 1.3;
}
.book-authors { 
    font-size: 11px; 
    color: #7f8c8d; 
    overflow: hidden; 
    display: -webkit-box; 
    -webkit-line-clamp: 1; 
    -webkit-box-orient: vertical;
    font-weight: 500;
}
.fav-btn { 
    font-size: 14px; 
    margin-top: 8px; 
    padding: 6px 12px; 
    border: none; 
    border-radius: 6px; 
    cursor: pointer; 
    background: #ecf0f1; 
    transition: 0.3s; 
    width: 100%;
}
.fav-btn:hover {
    background: #e74c3c;
    color: white;
}
.fav-btn.fav-active { 
    background: #e74c3c; 
    color: white;
}
.load-more-btn {
    background: linear-gradient(135deg, #3498db, #2980b9);
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    width: 100%;
    margin-top: 10px;
}
.load-more-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(52, 152, 219, 0.4);
}
.load-more-btn:disabled {
    background: #bdc3c7;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
}
.sidebar-book {
    display: flex;
    align-items: center;
    padding: 10px;
    margin-bottom: 8px;
    background: rgba(255,255,255,0.1);
    border-radius: 6px;
    transition: 0.3s;
}
.sidebar-book:hover {
    background: rgba(255,255,255,0.2);
}
#detail-overlay { 
    display: none; 
    position: fixed; 
    top: 0; 
    left: 0; 
    width: 100%; 
    height: 100%; 
    background: rgba(0,0,0,0.7); 
    z-index: 1000; 
    backdrop-filter: blur(5px);
}
#detail-box { 
    position: absolute; 
    background: white; 
    border-radius: 12px; 
    padding: 24px; 
    max-width: 600px; 
    box-shadow: 0 20px 60px rgba(0,0,0,0.3); 
    color: #2c3e50;
    border: 1px solid rgba(255,255,255,0.2);
}
#detail-close { 
    position: absolute; 
    top: 12px; 
    right: 16px; 
    cursor: pointer; 
    font-size: 24px; 
    font-weight: bold; 
    color: #7f8c8d;
    transition: 0.3s;
}
#detail-close:hover {
    color: #e74c3c;
}
#detail-content { 
    line-height: 1.6; 
    font-size: 14px; 
    color: #2c3e50;
}
.no-books {
    text-align: center;
    color: #7f8c8d;
    font-style: italic;
    padding: 40px;
    font-size: 16px;
}
.scroll-container::-webkit-scrollbar {
    width: 6px;
}
.scroll-container::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 3px;
}
.scroll-container::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 3px;
}
.scroll-container::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
}
""") as demo:

    with gr.Row(elem_classes="app-container"):
        with gr.Column(elem_classes="main-content"):
            gr.Markdown("# 📚 Book Explorer", elem_classes="main-title")
            
            # ---------- Random Books Section ----------
            with gr.Column(elem_classes="section-container"):
                gr.Markdown("🎲 Random Books", elem_classes="section-header")
                
                random_loaded_state = gr.State(df.sample(frac=1).reset_index(drop=True))
                random_display_state = gr.State(pd.DataFrame())
                random_page_state = gr.State(0)
                
                with gr.Column(elem_classes="scroll-container"):
                    random_container = gr.HTML()
                
                random_load_btn = gr.Button("📚 Load More Random Books", elem_classes="load-more-btn")

            # ---------- Popular Books Section ----------
            with gr.Column(elem_classes="section-container"):
                gr.Markdown("🔥 Popular Books", elem_classes="section-header")
                
                popular_loaded_state = gr.State(df.head(len(df)))
                popular_display_state = gr.State(pd.DataFrame())
                popular_page_state = gr.State(0)
                
                with gr.Column(elem_classes="scroll-container"):
                    popular_container = gr.HTML()
                
                popular_load_btn = gr.Button("📚 Load More Popular Books", elem_classes="load-more-btn")

            # ---------- Load more logic ----------
            def load_more(loaded_books, display_books, page_idx):
                start = page_idx * BOOKS_PER_LOAD
                end = start + BOOKS_PER_LOAD
                new_books = loaded_books.iloc[start:end]
                
                if display_books is None or display_books.empty:
                    display_books = pd.DataFrame()
                
                if new_books.empty:
                    # No more books to load
                    combined = display_books
                    html = build_books_grid_html(combined)
                    return combined, gr.update(value=html), page_idx, gr.update(visible=False)
                
                combined = pd.concat([display_books, new_books], ignore_index=True)
                html = build_books_grid_html(combined)
                
                # Check if there are more books to load
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

            # ---------- Initial load ----------
            def initial_load(loaded_books):
                return load_more(loaded_books, pd.DataFrame(), 0)

            # Set initial values
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
            favorites_container = gr.HTML("<p style='color: rgba(255,255,255,0.8);'>No favorites yet. Click the ❤️ button on books to add them here.</p>")

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
        sidebarContent.innerHTML = "<p style='color: rgba(255,255,255,0.8);'>No favorites yet. Click the ❤️ button on books to add them here.</p>";
        return;
    }
    let html = "<div style='display: flex; flex-direction: column; gap: 8px;'>";
    favorites.forEach((book,id)=>{
        html += `<div class="sidebar-book" data-id="${id}">
            <img src="${escapeHtml(book.img)}" style="width:40px;height:55px;object-fit:cover;border-radius:4px;margin-right:10px;">
            <div style="font-size:12px; flex: 1;">
                <strong style="color: white;">${escapeHtml(book.title)}</strong><br>
                <span style="color: rgba(255,255,255,0.8);">${escapeHtml(book.authors)}</span>
            </div>
        </div>`;
    });
    html += "</div>";
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
            favBtn.innerHTML = '❤️';
        }else{
            favorites.set(bookId,{title,authors,img});
            favBtn.classList.add('fav-active');
            favBtn.innerHTML = '❤️ Added';
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
        <div style="display:flex;gap:20px;align-items:flex-start;">
            <img src="${img}" style="width:180px;height:auto;border-radius:8px;object-fit:cover;box-shadow:0 4px 12px rgba(0,0,0,0.2);">
            <div style="flex:1;">
                <h2 style="margin:0 0 12px 0;color:#2c3e50;font-size:20px;line-height:1.3;">${escapeHtml(title)}</h2>
                <p style="margin:0 0 8px 0;color:#34495e;"><strong>Author(s):</strong> ${escapeHtml(authors)}</p>
                <p style="margin:0 0 12px 0;color:#34495e;"><strong>Genres:</strong> ${escapeHtml(genres)}</p>
                <div style="margin-top:12px;color:#2c3e50;line-height:1.6;max-height:200px;overflow-y:auto;padding-right:10px;">${escapeHtml(desc)}</div>
            </div>
        </div>
    `;

    // Center the detail box
    box.style.left = '50%';
    box.style.top = '50%';
    box.style.transform = 'translate(-50%, -50%)';

    overlay.style.display='block';
});

closeBtn.addEventListener('click',()=>{
    overlay.style.display='none';
    box.style.transform = 'translate(-50%, -50%)';
});
overlay.addEventListener('click',e=>{
    if(e.target===overlay) {
        overlay.style.display='none';
        box.style.transform = 'translate(-50%, -50%)';
    }
});
document.addEventListener('keydown',e=>{
    if(e.key==='Escape') {
        overlay.style.display='none';
        box.style.transform = 'translate(-50%, -50%)';
    }
});

// Initialize favorite buttons on existing cards
function initializeFavButtons() {
    document.querySelectorAll('.book-card').forEach(card => {
        const favBtn = card.querySelector('.fav-btn');
        const bookId = card.dataset.id;
        if (favorites.has(bookId)) {
            favBtn.classList.add('fav-active');
            favBtn.innerHTML = '❤️ Added';
        }
    });
}

// Reinitialize when new content loads
const observer = new MutationObserver(initializeFavButtons);
observer.observe(document.body, { childList: true, subtree: true });
initializeFavButtons();
</script>
""")

demo.launch()