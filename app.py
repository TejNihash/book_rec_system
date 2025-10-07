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

def build_books_grid_html(books_df):
    cards_html = [create_book_card_html(book) for _, book in books_df.iterrows()]
    return f"<div class='books-grid'>{''.join(cards_html)}</div>"

def search_books(df, query):
    query = query.lower()
    mask = df["title"].str.lower().str.contains(query) | \
           df["authors"].apply(lambda x: any(query in a.lower() for a in x)) | \
           df["genres"].apply(lambda x: any(query in g.lower() for g in x))
    return df[mask].reset_index(drop=True)

# ---------- Gradio UI ----------
with gr.Blocks(css="""
/* --- Books Grid --- */
.books-section { border:1px solid #555; border-radius:12px; padding:16px; height:400px; overflow-y:auto; margin-bottom:20px; background:#222; }
.books-grid { display:grid; grid-template-columns:repeat(6,1fr); gap:16px; }
.book-card { background:#333; border-radius:12px; padding:10px; box-shadow:0 3px 10px rgba(0,0,0,0.5); cursor:pointer; text-align:left; transition:all 0.3s ease; border:1px solid #555; height:100%; display:flex; flex-direction:column; color:#eee; }
.book-card:hover { transform:translateY(-4px) scale(1.02); box-shadow:0 8px 20px rgba(0,0,0,0.7); border-color:#667eea; }
.book-image-container { position:relative; margin-bottom:10px; }
.book-card img { width:100%; height:180px; object-fit:cover; border-radius:8px; border:1px solid #666; }
.book-badge { position:absolute; top:8px; right:8px; background:rgba(102,126,234,0.9); color:white; padding:2px 6px; border-radius:10px; font-size:10px; font-weight:bold;}
.book-info { flex-grow:1; display:flex; flex-direction:column; gap:4px; }
.book-title { font-size:13px; font-weight:700; color:#fff; line-height:1.3; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; margin-bottom:2px; }
.book-authors { font-size:11px; color:#88c; font-weight:600; overflow:hidden; display:-webkit-box; -webkit-line-clamp:1; -webkit-box-orient:vertical; margin-bottom:3px;}
.book-rating { font-size:10px; color:#ffa500; margin-bottom:4px; }
.book-meta { display:flex; flex-direction:column; gap:2px; margin-top:auto; font-size:10px; color:#ccc; }

/* --- Buttons --- */
.load-more-btn, .search-btn { background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); color:white; border:none; padding:10px 25px; border-radius:20px; font-weight:600; cursor:pointer; transition:all 0.3s ease; box-shadow:0 4px 12px rgba(102,126,234,0.3); font-size:12px; }
.load-more-btn:hover, .search-btn:hover { transform:translateY(-2px); box-shadow:0 6px 16px rgba(102,126,234,0.4); }

/* --- Card-Adjacent Popup --- */
#card-details-popup { position:absolute; background:#111; color:#eee; padding:16px; border-radius:12px; box-shadow:0 10px 30px rgba(0,0,0,0.7); max-width:320px; z-index:9999; display:none; }
#card-details-popup h3, #card-details-popup p, #card-details-popup span { color:#eee; }
#card-details-popup-close { position:absolute; top:6px; right:8px; cursor:pointer; font-weight:bold; font-size:18px; }
.description-scroll { max-height:150px; overflow:auto; border:1px solid #444; padding:4px; border-radius:6px; margin-top:6px; }

/* --- Section Titles --- */
.section-title { font-size:18px; font-weight:bold; color:#fff; margin-bottom:10px; }
""") as demo:

    gr.Markdown("# 📚 Dark Book Discovery Hub")
    gr.Markdown("### Explore our curated collection of amazing books")

    # ---------- Search ----------
    search_input = gr.Textbox(label="Search books (title, authors, genres)", placeholder="Type to search...")
    search_btn = gr.Button("Search", elem_classes="search-btn")
    clear_search_btn = gr.Button("Clear Search", elem_classes="search-btn")

    # ---------- Random Books Section ----------
    gr.Markdown("## 🎲 Random Books")
    random_books_container = gr.HTML(elem_classes="books-section")

    random_load_more_btn = gr.Button("📚 Load More Random Books", elem_classes="load-more-btn")
    shuffle_btn = gr.Button("🔀 Shuffle Random Books", elem_classes="load-more-btn")

    # ---------- Popular Books Section ----------
    gr.Markdown("## 📈 Popular Books")
    popular_books_container = gr.HTML(elem_classes="books-section")
    popular_load_more_btn = gr.Button("📚 Load More Popular Books", elem_classes="load-more-btn")

    # ---------- Favorites Section ----------
    gr.Markdown("## ❤️ Favorites")
    favorites_container = gr.HTML(elem_classes="books-section")

    # ---------- States ----------
    random_books_state = gr.State(df.sample(frac=1).reset_index(drop=True))
    random_display_state = gr.State(pd.DataFrame())
    random_index_state = gr.State(0)

    popular_books_state = gr.State(df.copy())
    popular_display_state = gr.State(pd.DataFrame())
    popular_index_state = gr.State(0)

    favorites_state = gr.State(pd.DataFrame(columns=df.columns))

    # ---------- Functions ----------
    def load_more_random(loaded_books, display_books, page_idx):
        start = page_idx * BOOKS_PER_LOAD
        end = start + BOOKS_PER_LOAD
        new_books = loaded_books.iloc[start:end]
        if new_books.empty:
            return display_books, gr.update(value=build_books_grid_html(display_books)), gr.update(visible=False), page_idx
        combined = pd.concat([display_books,new_books],ignore_index=True)
        html = build_books_grid_html(combined)
        return combined, gr.update(value=html), gr.update(visible=True), page_idx+1

    def shuffle_random_books(loaded_books, display_books):
        shuffled = loaded_books.sample(frac=1).reset_index(drop=True)
        initial_books = shuffled.iloc[:BOOKS_PER_LOAD]
        html = build_books_grid_html(initial_books)
        return shuffled, initial_books, html, 1

    def load_more_popular(loaded_books, display_books, page_idx):
        start = page_idx * BOOKS_PER_LOAD
        end = start + BOOKS_PER_LOAD
        new_books = loaded_books.iloc[start:end]
        if new_books.empty:
            return display_books, gr.update(value=build_books_grid_html(display_books)), gr.update(visible=False), page_idx
        combined = pd.concat([display_books,new_books],ignore_index=True)
        html = build_books_grid_html(combined)
        return combined, gr.update(value=html), gr.update(visible=True), page_idx+1

    def search_random_books(query):
        if not query.strip():
            books = random_books_state.value
        else:
            books = search_books(random_books_state.value, query)
        initial_books = books.iloc[:BOOKS_PER_LOAD]
        html = build_books_grid_html(initial_books)
        return books, initial_books, html, 1

    def clear_search():
        books = random_books_state.value
        initial_books = books.iloc[:BOOKS_PER_LOAD]
        html = build_books_grid_html(initial_books)
        return books, initial_books, html, 1

    # ---------- Event Handlers ----------
    random_load_more_btn.click(load_more_random,
        [random_books_state, random_display_state, random_index_state],
        [random_display_state, random_books_container, random_load_more_btn, random_index_state]
    )

    shuffle_btn.click(shuffle_random_books,
        [random_books_state, random_display_state],
        [random_books_state, random_display_state, random_books_container, random_index_state]
    )

    popular_load_more_btn.click(load_more_popular,
        [popular_books_state, popular_display_state, popular_index_state],
        [popular_display_state, popular_books_container, popular_load_more_btn, popular_index_state]
    )

    search_btn.click(search_random_books,
        [search_input],
        [random_books_state, random_display_state, random_books_container, random_index_state]
    )

    clear_search_btn.click(clear_search,
        None,
        [random_books_state, random_display_state, random_books_container, random_index_state]
    )

    # ---------- Initial Load ----------
    def initial_load(df_):
        initial_books = df_.iloc[:BOOKS_PER_LOAD]
        html = build_books_grid_html(initial_books)
        return initial_books, html, 1

    random_display_state.value, random_books_container.value, random_index_state.value = initial_load(random_books_state.value)
    popular_display_state.value, popular_books_container.value, popular_index_state.value = initial_load(popular_books_state.value)

    # ---------- Details Popup with Add to Favorites ----------
    gr.HTML("""
    <div id="card-details-popup">
        <span id="card-details-popup-close">&times;</span>
        <div id="card-details-popup-content"></div>
        <button id="add-to-favorites" style="margin-top:10px;background:#667eea;color:white;padding:6px 12px;border:none;border-radius:6px;cursor:pointer;">Add to Favorites</button>
    </div>

    <script>
    (function(){
        const portal = document.getElementById('card-details-popup');
        const content = document.getElementById('card-details-popup-content');
        const closeBtn = document.getElementById('card-details-popup-close');
        const favBtn = document.getElementById('add-to-favorites');

        let lastBookId = null;

        function showPopup(card){
            lastBookId = card.dataset.id;
            content.innerHTML = `
                <h3>${card.dataset.title}</h3>
                <p><strong>Author(s):</strong> ${card.dataset.authors}</p>
                <p><strong>Genres:</strong> ${card.dataset.genres}</p>
                <p><strong>Rating:</strong> ${card.dataset.rating}</p>
                <p><strong>Year:</strong> ${card.dataset.year}</p>
                <p><strong>Pages:</strong> ${card.dataset.pages}</p>
                <div class="description-scroll">${card.dataset.desc}</div>
            `;
            const rect = card.getBoundingClientRect();
            let top = window.scrollY + rect.top;
            let left = window.scrollX + rect.right + 10;
            if(left + 320 > window.innerWidth){
                left = window.scrollX + rect.left - 330;
            }
            portal.style.top = top + 'px';
            portal.style.left = left + 'px';
            portal.style.display = 'block';
        }

        function closePopup(){
            portal.style.display = 'none';
            lastBookId = null;
        }

        closeBtn.addEventListener('click', closePopup);
        document.addEventListener('keydown', e=>{ if(e.key==='Escape') closePopup(); });
        document.addEventListener('click', e=>{
            if(!e.target.closest('.book-card') && !e.target.closest('#card-details-popup')){
                closePopup();
            }
        });

        document.addEventListener('click', function(e){
            const card = e.target.closest('.book-card');
            if(!card) return;
            showPopup(card);
        });

        favBtn.addEventListener('click', function(){
            if(!lastBookId) return;
            document.querySelector('input[id^="component"]').value = lastBookId; // set hidden textbox
            document.querySelector('input[id^="component"]').dispatchEvent(new Event('change'));
            alert("Added to Favorites!");
        });

    })();
    </script>
    """)

    # Hidden Textbox to receive book ID from JS
    favorite_trigger = gr.Textbox(visible=False)
    
    # Python function to handle favorites
    def add_to_favorites(book_id, all_books, favorites):
        book_row = all_books[all_books["id"]==book_id]
        if book_row.empty or book_id in favorites["id"].values:
            return gr.update(value=build_books_grid_html(favorites)), favorites
        new_fav = pd.concat([favorites, book_row], ignore_index=True)
        return gr.update(value=build_books_grid_html(new_fav)), new_fav
    
    favorite_trigger.change(
        add_to_favorites,
        [favorite_trigger, random_books_state, favorites_state],
        [favorites_container, favorites_state]
    )


demo.launch()
