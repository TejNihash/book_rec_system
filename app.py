import ast
import pandas as pd
import gradio as gr
import random

# ---------- Load dataset ----------
df = pd.read_csv("data_mini_books.csv")
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["rating"] = df.get("rating", [random.uniform(3.5, 4.8) for _ in range(len(df))])
df["year"] = df.get("year", [random.randint(1990, 2023) for _ in range(len(df))])
df["pages"] = df.get("pages", [random.randint(150, 600) for _ in range(len(df))])

BOOKS_PER_LOAD = 12

# ---------- Favorites Storage ----------
favorites_list = []

# ---------- Helpers ----------
def create_book_card_html(book):
    rating = book.get("rating", 0)
    stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
    if rating % 1 >= 0.5:
        stars = "⭐" * (int(rating)+1) + "☆" * (4 - int(rating))
    description = book.get("description", "No description available.")
    return f"""
    <div class='book-card' data-id='{book["id"]}' data-title="{book['title']}" 
         data-authors="{', '.join(book['authors'])}" data-genres="{', '.join(book['genres'])}" 
         data-img="{book['image_url']}" data-desc="{description}"
         data-rating="{rating}" data-year="{book.get('year', 'N/A')}" data-pages="{book.get('pages', 'N/A')}">
        <div class='book-image-container'>
            <img src="{book['image_url']}" onerror="this.src='https://via.placeholder.com/150x220/444/fff?text=No+Image'">
            <div class='book-badge'>{book.get('year', 'N/A')}</div>
        </div>
        <div class='book-info'>
            <div class='book-title'>{book['title']}</div>
            <div class='book-authors'>by {', '.join(book['authors'])}</div>
            <div class='book-rating'>{stars} ({rating:.1f})</div>
            <div class='book-meta'>
                <span class='book-pages'>{book.get('pages', 'N/A')} pages</span>
                <span class='book-genres'>{', '.join(book['genres'][:2])}{'...' if len(book['genres'])>2 else ''}</span>
            </div>
        </div>
    </div>
    """

def build_books_grid_html(books_df):
    if books_df.empty:
        return "<div style='text-align:center; color:#888; padding:40px;'>No books found</div>"
    return f"<div class='books-grid'>{''.join([create_book_card_html(book) for _, book in books_df.iterrows()])}</div>"

def add_to_favorites(book_id):
    global favorites_list
    book = df[df['id']==book_id]
    if not book.empty and all(fav['id'] != book_id for fav in favorites_list):
        favorites_list.append(book.iloc[0].to_dict())
    return build_books_grid_html(pd.DataFrame(favorites_list))

# ---------- Gradio UI ----------
with gr.Blocks(css="""
.books-section { border:1px solid #555; border-radius:12px; padding:16px; height:400px; overflow-y:auto; margin-bottom:20px; background:#222; }
.books-grid { display:grid; grid-template-columns:repeat(6,1fr); gap:16px; }
.book-card { background:#333; border-radius:12px; padding:10px; box-shadow:0 3px 10px rgba(0,0,0,0.5); cursor:pointer; text-align:left; transition:all 0.3s ease; border:1px solid #555; color:#eee; display:flex; flex-direction:column; }
.book-card:hover { transform:translateY(-4px) scale(1.02); box-shadow:0 8px 20px rgba(0,0,0,0.7); border-color:#667eea; }
.book-image-container { position:relative; margin-bottom:10px; }
.book-card img { width:100%; height:180px; object-fit:cover; border-radius:8px; border:1px solid #666; }
.book-badge { position:absolute; top:8px; right:8px; background:rgba(102,126,234,0.9); color:white; padding:2px 6px; border-radius:10px; font-size:10px; font-weight:bold;}
.book-info { flex-grow:1; display:flex; flex-direction:column; gap:4px; }
.book-title { font-size:13px; font-weight:700; color:#fff; line-height:1.3; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; margin-bottom:2px; }
.book-authors { font-size:11px; color:#88c; font-weight:600; overflow:hidden; display:-webkit-box; -webkit-line-clamp:1; -webkit-box-orient:vertical; margin-bottom:3px;}
.book-rating { font-size:10px; color:#ffa500; margin-bottom:4px; }
.book-meta { display:flex; flex-direction:column; gap:2px; margin-top:auto; font-size:10px; color:#ccc; }

.favorite-btn { background:linear-gradient(135deg,#ed8936 0%,#dd6b20 100%); color:white; border:none; padding:10px 20px; border-radius:20px; font-weight:600; cursor:pointer; transition:all 0.3s ease; margin-top:15px; width:100%; font-size:14px; }
.favorite-btn:hover { transform:translateY(-2px); box-shadow:0 6px 16px rgba(237,137,54,0.4); }

/* Popup */
.popup-overlay { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.6); z-index:9998; }
.popup-container { display:none; position:absolute; background:#111; border-radius:16px; padding:24px; max-width:400px; width:90%; box-shadow:0 20px 60px rgba(0,0,0,0.7); border:2px solid #667eea; z-index:9999; color:#eee; }
.popup-close { position:absolute; top:8px; right:8px; cursor:pointer; font-size:20px; font-weight:bold; color:#fff; background:#222; border-radius:50%; width:28px; height:28px; display:flex; align-items:center; justify-content:center; }
.popup-close:hover { background:#667eea; color:white; }
.popup-content { line-height:1.6; }
""") as demo:

    gr.Markdown("# 📚 Dark Book Discovery Hub")
    gr.Markdown("### Explore our curated collection of amazing books")

    # Random Books
    gr.Markdown("## 🎲 Random Books")
    random_container = gr.HTML(elem_classes="books-section")
    random_state = gr.State(df.sample(frac=1).reset_index(drop=True))

    # Favorites
    gr.Markdown("## ⭐ Favorites")
    favorites_container = gr.HTML(elem_classes="books-section")
    favorites_state = gr.State(pd.DataFrame(favorites_list))

    # ---------- Initial load ----------
    def initial_load(df_):
        html = build_books_grid_html(df_.iloc[:BOOKS_PER_LOAD])
        return html

    random_container.value = initial_load(random_state.value)
    favorites_container.value = build_books_grid_html(pd.DataFrame(favorites_list))

    # ---------- Hidden Favorite Trigger ----------
    favorite_id = gr.Textbox(visible=False)
    trigger_fav = gr.Button("TriggerFav", visible=False)

    trigger_fav.click(lambda book_id: add_to_favorites(book_id),
                      inputs=[favorite_id],
                      outputs=[favorites_container])

    # ---------- Popup HTML ----------
    gr.HTML("""
    <div class="popup-overlay" id="popup-overlay"></div>
    <div class="popup-container" id="popup-container">
        <span class="popup-close" id="popup-close">&times;</span>
        <div class="popup-content" id="popup-content"></div>
    </div>

    <script>
    const overlay = document.getElementById('popup-overlay');
    const container = document.getElementById('popup-container');
    const content = document.getElementById('popup-content');
    const closeBtn = document.getElementById('popup-close');

    document.addEventListener('click', function(e){
        const card = e.target.closest('.book-card');
        if(!card) return;

        const rect = card.getBoundingClientRect();
        container.style.top = (rect.top + window.scrollY) + 'px';
        container.style.left = (rect.right + 10 + window.scrollX) + 'px';

        const html = `
            <h3 style="margin:0 0 10px 0;">${card.dataset.title}</h3>
            <p><strong>Author(s):</strong> ${card.dataset.authors}</p>
            <p><strong>Genres:</strong> ${card.dataset.genres}</p>
            <button class="favorite-btn" onclick="setHiddenFavoriteIdAndTrigger('${card.dataset.id}')">❤️ Add to Favorites</button>
        `;
        content.innerHTML = html;
        overlay.style.display = 'block';
        container.style.display = 'block';
    });

    function closePopup(){
        overlay.style.display = 'none';
        container.style.display = 'none';
    }

    closeBtn.addEventListener('click', closePopup);
    overlay.addEventListener('click', closePopup);

    function setHiddenFavoriteIdAndTrigger(bookId){
        const input = document.querySelector('input[type=text][style*="display:none"]');
        const btn = document.querySelector('button:contains("TriggerFav")');
        if(!input){ console.warn("Hidden favorite input not found"); return; }
        input.value = bookId;
        input.dispatchEvent(new Event('input', {bubbles:true}));
        input.dispatchEvent(new Event('change', {bubbles:true}));
        setTimeout(()=>{ btn.click(); closePopup(); }, 50);
    }
    </script>
    """)

demo.launch()
