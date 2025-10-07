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

# ---------- Gradio UI ----------
with gr.Blocks(css="""
/* --- Books Grid --- */
.books-section { border:1px solid #555; border-radius:12px; padding:16px; height:500px; overflow-y:auto; margin-bottom:20px; background:#222; }
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
.load-more-btn { background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); color:white; border:none; padding:10px 25px; border-radius:20px; font-weight:600; cursor:pointer; transition:all 0.3s ease; box-shadow:0 4px 12px rgba(102,126,234,0.3); font-size:12px; }
.load-more-btn:hover { transform:translateY(-2px); box-shadow:0 6px 16px rgba(102,126,234,0.4); }

/* --- Popup Portal --- */
#floating-portal-popup { position:fixed; top:50%; left:50%; transform:translate(-50%,-50%) scale(0.8); z-index:99999; width:80%; max-width:700px; max-height:80vh; overflow-y:auto; background:#111; color:#eee; border-radius:16px; padding:24px; box-shadow:0 20px 60px rgba(0,0,0,0.7); opacity:0; transition: all 0.3s ease;}
#floating-portal-popup h2, #floating-portal-popup p, #floating-portal-popup span { color:#eee; }
#floating-portal-close { position:absolute; top:12px; right:16px; cursor:pointer; font-size:24px; font-weight:bold; color:#fff; background:#222; border-radius:50%; width:32px; height:32px; display:flex; align-items:center; justify-content:center; box-shadow:0 2px 6px rgba(0,0,0,0.5); }
#floating-portal-close:hover { background:#667eea; color:white; }
.description-scroll { max-height:200px; overflow-y:auto; padding-right:8px; margin-top:10px; background:#222; border-radius:6px; padding:8px; border:1px solid #444;}
.description-scroll::-webkit-scrollbar { width:6px; }
.description-scroll::-webkit-scrollbar-thumb { background:#667eea; border-radius:3px; }

""") as demo:

    gr.Markdown("# 📚 Dark Book Discovery Hub", elem_classes="dark-title")
    gr.Markdown("### Explore our curated collection of amazing books", elem_classes="dark-subtitle")

    # ---------- Floating Portal Popup ----------
    gr.HTML("""
    <div id="floating-portal-popup">
        <span id="floating-portal-close">&times;</span>
        <div id="floating-portal-content"></div>
    </div>

    <script>
    (function(){
        const portal = document.getElementById('floating-portal-popup');
        const content = portal.querySelector('#floating-portal-content');
        const closeBtn = portal.querySelector('#floating-portal-close');
        let lastScrollY = 0;

        function showPopup(html) {
            content.innerHTML = html;
            portal.style.opacity='1';
            portal.style.transform='translate(-50%,-50%) scale(1)';
            document.body.style.overflow='hidden';
        }

        function closePopup(){
            portal.style.opacity='0';
            portal.style.transform='translate(-50%,-50%) scale(0.8)';
            document.body.style.overflow='auto';
            window.scrollTo({top:lastScrollY, behavior:'auto'});
            setTimeout(()=>content.innerHTML='',300);
        }

        closeBtn.addEventListener('click', closePopup);
        document.addEventListener('keydown', e=>{ if(e.key==='Escape') closePopup(); });
        portal.addEventListener('click', e=>e.stopPropagation());

        document.addEventListener('click', function(e){
            const card = e.target.closest('.book-card');
            if(!card) return;

            lastScrollY = window.scrollY || window.pageYOffset;

            const html = `
                <div style="display:flex; gap:20px; align-items:flex-start; margin-bottom:20px;">
                    <img src="${card.dataset.img}" style="width:180px; height:auto; border-radius:8px; object-fit:cover;">
                    <div style="flex:1;">
                        <h2>${card.dataset.title}</h2>
                        <p><strong>Author(s):</strong> ${card.dataset.authors}</p>
                        <p><strong>Genres:</strong> ${card.dataset.genres}</p>
                        <p><strong>Rating:</strong> ${card.dataset.rating}</p>
                        <p><strong>Year:</strong> ${card.dataset.year}</p>
                        <p><strong>Pages:</strong> ${card.dataset.pages}</p>
                        <div class="description-scroll">${card.dataset.desc}</div>
                    </div>
                </div>
            `;
            showPopup(html);
        });
    })();
    </script>
    """)

    # ---------- Random Books ----------
    gr.Markdown("## 🎲 Random Books")
    with gr.Column():
        random_books_container = gr.HTML(elem_classes="books-section")
        with gr.Row():
            random_load_more_btn = gr.Button("📚 Load More Random Books", elem_classes="load-more-btn")
            shuffle_btn = gr.Button("🔀 Shuffle Books", elem_classes="load-more-btn")

    # ---------- Popular Books ----------
    gr.Markdown("## 📈 Popular Books")
    with gr.Column():
        popular_books_container = gr.HTML(elem_classes="books-section")
        with gr.Row():
            popular_load_more_btn = gr.Button("📚 Load More Popular Books", elem_classes="load-more-btn")

    # ---------- States ----------
    random_books_state = gr.State(df.sample(frac=1).reset_index(drop=True))
    random_display_state = gr.State(pd.DataFrame())
    random_index_state = gr.State(0)

    popular_books_state = gr.State(df.copy())
    popular_display_state = gr.State(pd.DataFrame())
    popular_index_state = gr.State(0)

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

    def load_more_popular(loaded_books, display_books, page_idx):
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

    # ---------- Initial Load ----------
    def initial_load(df_):
        initial_books = df_.iloc[:BOOKS_PER_LOAD]
        html = build_books_grid_html(initial_books)
        return initial_books, html, 1

    random_display_state.value, random_books_container.value, random_index_state.value = initial_load(random_books_state.value)
    popular_display_state.value, popular_books_container.value, popular_index_state.value = initial_load(popular_books_state.value)

demo.launch()
