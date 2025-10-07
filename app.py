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

# ---------- Helpers ----------
def create_book_card_html(book, favorites):
    is_fav = book["id"] in favorites
    rating = book.get("rating", 0)
    stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
    if rating % 1 >= 0.5:
        stars = "⭐" * (int(rating)+1) + "☆" * (4 - int(rating))
    description = book.get("description", "No description available.")
    heart_class = "❤️" if is_fav else "🤍"
    return f"""
    <div class='book-card' data-id='{book["id"]}' data-title="{book['title']}" 
         data-authors="{', '.join(book['authors'])}" data-genres="{', '.join(book['genres'])}" 
         data-img="{book['image_url']}" data-desc="{description}"
         data-rating="{rating}" data-year="{book.get('year', 'N/A')}" data-pages="{book.get('pages', 'N/A')}">
        <div class='book-image-container'>
            <img src="{book['image_url']}" onerror="this.src='https://via.placeholder.com/150x220/444/fff?text=No+Image'">
            <div class='book-badge'>{book.get('year', 'N/A')}</div>
            <div class='book-fav-icon' data-id="{book['id']}">{heart_class}</div>
        </div>
        <div class='book-info'>
            <div class='book-title' title="{book['title']}">{book['title']}</div>
            <div class='book-authors'>by {', '.join(book['authors'])}</div>
            <div class='book-rating'>{stars} ({rating:.1f})</div>
            <div class='book-meta'>
                <span class='book-pages'>{book.get('pages', 'N/A')} pages</span>
                <span class='book-genres'>{', '.join(book['genres'][:2])}{'...' if len(book['genres'])>2 else ''}</span>
            </div>
        </div>
    </div>
    """

def build_books_grid_html(books_df, favorites):
    cards_html = [create_book_card_html(book, favorites) for _, book in books_df.iterrows()]
    return f"<div class='books-grid'>{''.join(cards_html)}</div>"

# ---------- Gradio UI ----------
with gr.Blocks(css="""
.books-section { border:1px solid #555; border-radius:12px; padding:16px; height:500px; overflow-y:auto; margin-bottom:20px; background:#222; }
.books-grid { display:grid; grid-template-columns:repeat(6,1fr); gap:16px; }
.book-card { background:#333; border-radius:12px; padding:10px; box-shadow:0 3px 10px rgba(0,0,0,0.5); cursor:pointer; text-align:left; transition:all 0.3s ease; border:1px solid #555; height:100%; display:flex; flex-direction:column; color:#eee; position:relative; }
.book-card:hover { transform:translateY(-4px) scale(1.02); box-shadow:0 8px 20px rgba(0,0,0,0.7); border-color:#667eea; }
.book-image-container { position:relative; margin-bottom:10px; }
.book-card img { width:100%; height:180px; object-fit:cover; border-radius:8px; border:1px solid #666; }
.book-badge { position:absolute; top:8px; right:8px; background:rgba(102,126,234,0.9); color:white; padding:2px 6px; border-radius:10px; font-size:10px; font-weight:bold;}
.book-fav-icon { position:absolute; top:8px; left:8px; font-size:20px; cursor:pointer; }
.book-info { flex-grow:1; display:flex; flex-direction:column; gap:4px; }
.book-title { font-size:13px; font-weight:700; color:#fff; line-height:1.3; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; margin-bottom:2px; }
.book-authors { font-size:11px; color:#88c; font-weight:600; overflow:hidden; display:-webkit-box; -webkit-line-clamp:1; -webkit-box-orient:vertical; margin-bottom:3px;}
.book-rating { font-size:10px; color:#ffa500; margin-bottom:4px; }
.book-meta { display:flex; flex-direction:column; gap:2px; margin-top:auto; font-size:10px; color:#ccc; }
.description-scroll { max-height:200px; overflow-y:auto; padding-right:8px; margin-top:10px; background:#222; border-radius:6px; padding:8px; border:1px solid #444;}

.load-more-btn { background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); color:white; border:none; padding:10px 25px; border-radius:20px; font-weight:600; cursor:pointer; transition:all 0.3s ease; box-shadow:0 4px 12px rgba(102,126,234,0.3); font-size:12px; }
.load-more-btn:hover { transform:translateY(-2px); box-shadow:0 6px 16px rgba(102,126,234,0.4); }

/* Popup next to card */
#floating-portal-popup { position:absolute; z-index:99999; width:300px; max-height:400px; overflow-y:auto; background:#111; color:#eee; border-radius:16px; padding:16px; box-shadow:0 10px 30px rgba(0,0,0,0.7); display:none;}
#floating-portal-popup h2, #floating-portal-popup p, #floating-portal-popup span { color:#eee; }
#floating-portal-close { position:absolute; top:8px; right:8px; cursor:pointer; font-size:20px; font-weight:bold; color:#fff; background:#222; border-radius:50%; width:28px; height:28px; display:flex; align-items:center; justify-content:center; }
#floating-portal-close:hover { background:#667eea; color:white; }
#floating-portal-fav { margin-top:10px; padding:6px 12px; border:none; border-radius:12px; background:#667eea; color:white; cursor:pointer; font-weight:600; }
#floating-portal-fav:hover { background:#764ba2; }
""") as demo:

    gr.Markdown("# 📚 Dark Book Discovery Hub")
    gr.Markdown("### Explore our curated collection of amazing books")

    # ---------- States ----------
    favorites_state = gr.State([])
    current_book_id_state = gr.State("")

    # ---------- Popup ----------
    popup = gr.HTML("""
    <div id="floating-portal-popup">
        <span id="floating-portal-close">&times;</span>
        <div id="floating-portal-content"></div>
        <button id="floating-portal-fav">❤️ Add to Favorites</button>
    </div>
    <script>
    (function(){
        const portal = document.getElementById('floating-portal-popup');
        const content = portal.querySelector('#floating-portal-content');
        const closeBtn = portal.querySelector('#floating-portal-close');
        const favBtn = portal.querySelector('#floating-portal-fav');
        let currentBookId = null;

        closeBtn.addEventListener('click', ()=>portal.style.display='none');
        document.addEventListener('keydown', e=>{ if(e.key==='Escape') portal.style.display='none'; });

        document.addEventListener('click', function(e){
            const card = e.target.closest('.book-card');
            const fav_icon = e.target.closest('.book-fav-icon');
            if(fav_icon){ // toggle favorite directly from card
                const bookId = fav_icon.dataset.id;
                const hiddenBtn = gradioApp().getElementById('hidden-add-fav');
                hiddenBtn.dataset.bookId = bookId;
                hiddenBtn.click();
                return;
            }
            if(!card) return;

            currentBookId = card.dataset.id;
            const html = `
                <h2>${card.dataset.title}</h2>
                <p><strong>Author(s):</strong> ${card.dataset.authors}</p>
                <p><strong>Genres:</strong> ${card.dataset.genres}</p>
                <p><strong>Rating:</strong> ${card.dataset.rating}</p>
                <p><strong>Year:</strong> ${card.dataset.year}</p>
                <p><strong>Pages:</strong> ${card.dataset.pages}</p>
                <div class="description-scroll">${card.dataset.desc}</div>
            `;
            content.innerHTML = html;

            const rect = card.getBoundingClientRect();
            let top = window.scrollY + rect.top;
            let left = window.scrollX + rect.right + 10;
            if(left + portal.offsetWidth > window.innerWidth) left = window.scrollX + rect.left - portal.offsetWidth - 10;
            portal.style.top = top+'px';
            portal.style.left = left+'px';
            portal.style.display = 'block';
        });

        favBtn.addEventListener('click', ()=>{
            if(currentBookId){
                const hiddenBtn = gradioApp().getElementById('hidden-add-fav');
                hiddenBtn.dataset.bookId = currentBookId;
                hiddenBtn.click();
            }
        });
    })();
    </script>
    """)

    # ---------- Hidden Button for Python ----------
    hidden_btn = gr.Button("Hidden Add Fav", visible=False, elem_id="hidden-add-fav")
    def toggle_fav(book_id, fav_list):
        if not book_id:
            return fav_list, gr.update()
        if book_id in fav_list:
            fav_list.remove(book_id)
        else:
            fav_list.append(book_id)
        fav_books = df[df['id'].isin(fav_list)]
        html = build_books_grid_html(fav_books, fav_list)
        return fav_list, gr.update(value=html)
    hidden_btn.click(toggle_fav, [gr.State(""), favorites_state], [favorites_state, hidden_btn])

    # ---------- Random Books ----------
    gr.Markdown("## 🎲 Random Books")
    random_books_container = gr.HTML(elem_classes="books-section")
    random_load_more_btn = gr.Button("📚 Load More Random Books", elem_classes="load-more-btn")
    shuffle_btn = gr.Button("🔀 Shuffle Books", elem_classes="load-more-btn")

    # ---------- Popular Books ----------
    gr.Markdown("## 📈 Popular Books")
    popular_books_container = gr.HTML(elem_classes="books-section")
    popular_load_more_btn = gr.Button("📚 Load More Popular Books", elem_classes="load-more-btn")

    # ---------- Favorites Section ----------
    gr.Markdown("## 💖 Favorites")
    favorites_container = gr.HTML(elem_classes="books-section")

    # ---------- Initial Load ----------
    def initial_load(df_, favorites):
        initial_books = df_.iloc[:BOOKS_PER_LOAD]
        html = build_books_grid_html(initial_books, favorites)
        return initial_books, html

    random_display_state = gr.State(df.sample(frac=1).reset_index(drop=True))
    popular_display_state = gr.State(df.copy())

    random_books_container.value = build_books_grid_html(random_display_state.value.iloc[:BOOKS_PER_LOAD], favorites_state.value)
    popular_books_container.value = build_books_grid_html(popular_display_state.value.iloc[:BOOKS_PER_LOAD], favorites_state.value)

demo.launch()
