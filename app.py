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

# ---------- Favorites System ----------
favorites_list = []

def toggle_favorite(book_id):
    """Toggle favorite status for a book"""
    global favorites_list
    
    book_match = df[df['id'] == book_id]
    if book_match.empty:
        return "❌ Book not found!"
    
    book_data = book_match.iloc[0].to_dict()
    
    # Toggle favorite
    if any(fav['id'] == book_id for fav in favorites_list):
        favorites_list = [fav for fav in favorites_list if fav['id'] != book_id]
        message = f"💔 Removed '{book_data['title']}' from favorites!"
    else:
        favorites_list.append(book_data)
        message = f"❤️ Added '{book_data['title']}' to favorites!"
    
    return message

# ---------- Helpers ----------
def create_book_card_html(book):
    is_favorite = any(fav['id'] == book["id"] for fav in favorites_list)
    fav_text = "💔 Remove" if is_favorite else "❤️ Add to Fav"
    fav_class = "favorite-btn remove" if is_favorite else "favorite-btn"
    
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
        <button class='{fav_class}' onclick='toggleFavorite("{book["id"]}")'>{fav_text}</button>
    </div>
    """

def build_books_grid_html(books_df):
    if books_df.empty:
        return "<div class='no-books'>No books found</div>"
    cards_html = [create_book_card_html(book) for _, book in books_df.iterrows()]
    return f"<div class='books-grid'>{''.join(cards_html)}</div>"

def display_favorites():
    """Display favorites section"""
    if not favorites_list:
        return "<div class='no-favorites'>No favorite books yet. Click 'Add to Fav' on any book!</div>"
    
    favorites_html = "<div class='favorites-grid'>"
    for book in favorites_list:
        favorites_html += f"""
        <div class='favorite-card'>
            <img src="{book['image_url']}" onerror="this.src='https://via.placeholder.com/80x120/667eea/white?text=No+Image'">
            <div class='fav-title'>{book['title']}</div>
            <div class='fav-authors'>{', '.join(book['authors'][:1])}</div>
        </div>
        """
    favorites_html += "</div>"
    return favorites_html

# ---------- Gradio UI ----------
with gr.Blocks(css="""
.books-section { border:1px solid #e0e0e0; border-radius:12px; padding:12px; 
                 max-height:500px; overflow-y:auto; margin-bottom:10px; background:#f7f7f7;}
.books-grid { display:grid; grid-template-columns: repeat(6,1fr); gap:12px; }
.book-card { background:#fff; border-radius:8px; padding:6px; box-shadow:0 2px 6px rgba(0,0,0,0.15);
            cursor:pointer; text-align:center; transition:all 0.2s ease; position: relative; }
.book-card:hover { transform:translateY(-2px); box-shadow:0 4px 12px rgba(0,0,0,0.25); }
.book-card img { width:100%; height:160px; object-fit:cover; border-radius:4px; margin-bottom:6px; }
.book-title { font-size:12px; font-weight:bold; color:#222; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; margin-bottom: 4px; }
.book-authors { font-size:10px; color:#555; overflow:hidden; display:-webkit-box; -webkit-line-clamp:1; -webkit-box-orient:vertical; margin-bottom: 8px; }

.favorite-btn { 
    background: #667eea; 
    color: white; 
    border: none; 
    padding: 6px 10px; 
    border-radius: 15px; 
    font-size: 10px; 
    cursor: pointer; 
    transition: all 0.2s ease;
    width: 100%;
}
.favorite-btn:hover { 
    background: #5a67d8; 
    transform: translateY(-1px);
}
.favorite-btn.remove { 
    background: #e53e3e; 
}
.favorite-btn.remove:hover { 
    background: #c53030;
}

.favorites-section { 
    border: 2px solid #667eea; 
    border-radius: 12px; 
    padding: 16px; 
    margin-top: 20px; 
    background: #f0f4ff;
}
.favorites-grid { 
    display: grid; 
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); 
    gap: 10px; 
    margin-top: 10px;
}
.favorite-card { 
    background: #fff; 
    border-radius: 8px; 
    padding: 8px; 
    text-align: center; 
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.favorite-card img { 
    width: 100%; 
    height: 100px; 
    object-fit: cover; 
    border-radius: 4px; 
    margin-bottom: 6px;
}
.fav-title { 
    font-size: 11px; 
    font-weight: bold; 
    color: #222; 
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    margin-bottom: 2px;
}
.fav-authors { 
    font-size: 9px; 
    color: #666; 
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
}
.no-favorites { 
    text-align: center; 
    color: #666; 
    padding: 20px; 
    font-style: italic;
}
.no-books { text-align: center; color: #666; padding: 40px; }

.feedback-message {
    background: #48bb78;
    color: white;
    padding: 10px 16px;
    border-radius: 8px;
    margin: 10px 0;
    text-align: center;
    font-weight: 600;
}

#detail-overlay { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.7); z-index:1000; }
#detail-box { position:absolute; background:#fff; border-radius:8px; padding:16px; max-width:600px; box-shadow:0 8px 20px rgba(0,0,0,0.35); color:#111; }
#detail-close { position:absolute; top:8px; right:12px; cursor:pointer; font-size:20px; font-weight:bold; }
#detail-content { line-height:1.5; font-size:14px; color:#111; }
""") as demo:

    gr.Markdown("# 🎲 Random & Popular Books")

    # Feedback message
    feedback = gr.HTML("")
    
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

    # ---------- Favorites Section ----------
    gr.Markdown("⭐ Your Favorite Books")
    favorites_container = gr.HTML(display_favorites())

    # ---------- Load more logic ----------
    def load_more(loaded_books, display_books, page_idx):
        start = page_idx * BOOKS_PER_LOAD
        end = start + BOOKS_PER_LOAD
        new_books = loaded_books.iloc[start:end]
        if new_books.empty:
            return display_books, gr.update(visible=False), page_idx
        combined = pd.concat([display_books, new_books], ignore_index=True)
        html = build_books_grid_html(combined)
        return combined, gr.update(value=html), page_idx+1

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

    # ---------- Favorite toggle logic ----------
    def handle_favorite_toggle(book_id):
        message = toggle_favorite(book_id)
        favorites_html = display_favorites()
        
        # Update both book sections to reflect favorite status changes
        random_html = build_books_grid_html(random_display_state.value)
        popular_html = build_books_grid_html(popular_display_state.value)
        
        feedback_html = f"<div class='feedback-message'>{message}</div>"
        
        return favorites_html, random_html, popular_html, feedback_html

    # ---------- Initial load ----------
    def initial_load(loaded_books):
        return load_more(loaded_books, pd.DataFrame(), 0)

    random_display_state.value, random_container.value, random_page_state.value = initial_load(random_loaded_state.value)
    popular_display_state.value, popular_container.value, popular_page_state.value = initial_load(popular_loaded_state.value)

    # ---------- Create hidden buttons for each book's favorite toggle ----------
    for _, book in df.iterrows():
        fav_btn = gr.Button(f"fav_{book['id']}", visible=False)
        fav_btn.click(
            lambda bid=book['id']: handle_favorite_toggle(bid),
            outputs=[favorites_container, random_container, popular_container, feedback]
        )

    # ---------- Detail popup ----------
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

function toggleFavorite(bookId) {
    // Find and click the corresponding hidden button
    const buttons = document.querySelectorAll('button');
    for (let btn of buttons) {
        if (btn.textContent.includes('fav_' + bookId)) {
            btn.click();
            break;
        }
    }
}

document.addEventListener('click', e=>{
    const card = e.target.closest('.book-card'); 
    if(!card) return;
    const title = card.dataset.title;
    const authors = card.dataset.authors;
    const genres = card.dataset.genres;
    const desc = card.dataset.desc;
    const img = card.dataset.img;
    const bookId = card.dataset.id;
    
    // Check if this book is a favorite
    const isFavorite = Array.from(document.querySelectorAll('.book-card'))
        .find(card => card.dataset.id === bookId)
        ?.querySelector('.favorite-btn')
        ?.textContent.includes('Remove');
    
    const favoriteText = isFavorite ? "💔 Remove from Favorites" : "❤️ Add to Favorites";
    
    document.getElementById('detail-content').innerHTML = `
        <div style="display:flex;gap:16px;align-items:flex-start;">
            <img src="${img}" style="width:220px;height:auto;border-radius:6px;object-fit:cover;">
            <div style="max-width:340px;">
                <h2 style="margin:0 0 8px 0; color:#222222;">${escapeHtml(title)}</h2>
                <p style="margin:0 0 4px 0; color:#222222;"><strong>Author(s):</strong> ${escapeHtml(authors)}</p>
                <p style="margin:0 0 6px 0; color:#222222;"><strong>Genres:</strong> ${escapeHtml(genres)}</p>
                <div style="margin-top:6px; color:#222222;">${escapeHtml(desc)}</div>
                <button onclick="toggleFavorite('${bookId}')" style="margin-top:12px; background:#667eea; color:white; border:none; padding:8px 16px; border-radius:6px; cursor:pointer;">${favoriteText}</button>
            </div>
        </div>
    `;
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