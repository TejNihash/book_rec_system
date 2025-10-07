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
        stars = "⭐" * (int(rating) + 1) + "☆" * (4 - int(rating))
    
    description = book.get('description', 'No description available.')
    
    return f"""
    <div class='book-card' data-id='{book["id"]}' data-title="{book['title']}" 
         data-authors="{', '.join(book['authors'])}" data-genres="{', '.join(book['genres'])}" 
         data-img="{book['image_url']}" data-desc="{description}"
         data-rating="{rating}" data-year="{book.get('year', 'N/A')}" data-pages="{book.get('pages', 'N/A')}">
        <div class='book-image-container'>
            <img src="{book['image_url']}" onerror="this.src='https://via.placeholder.com/150x220/667eea/white?text=No+Image'">
            <div class='book-badge'>{book.get('year', 'N/A')}</div>
        </div>
        <div class='book-info'>
            <div class='book-title' title="{book['title']}">{book['title']}</div>
            <div class='book-authors' title="{', '.join(book['authors'])}">by {', '.join(book['authors'])}</div>
            <div class='book-rating'>{stars} ({rating:.1f})</div>
            <div class='book-meta'>
                <span class='book-pages'>{book.get('pages', 'N/A')} pages</span>
                <span class='book-genres'>{', '.join(book['genres'][:2])}{'...' if len(book['genres']) > 2 else ''}</span>
            </div>
        </div>
    </div>
    """

def build_books_grid_html(books_df):
    cards_html = [create_book_card_html(book) for _, book in books_df.iterrows()]
    return f"<div class='books-grid'>{''.join(cards_html)}</div>"

# ---------- Gradio UI ----------
with gr.Blocks(css="""
.books-section { border:1px solid #e0e0e0; border-radius:12px; padding:16px; height:400px; overflow-y:auto; margin-bottom:20px; background:#222; }
.books-grid { display:grid; grid-template-columns:repeat(6,1fr); gap:16px; }
.book-card { background:#333; border-radius:12px; padding:10px; box-shadow:0 3px 10px rgba(0,0,0,0.5); cursor:pointer; color:#eee; height:100%; display:flex; flex-direction:column; transition:all 0.3s ease; }
.book-card:hover { transform:translateY(-4px) scale(1.02); box-shadow:0 8px 20px rgba(0,0,0,0.7); border-color:#667eea; }
.book-image-container { position:relative; margin-bottom:10px; }
.book-card img { width:100%; height:180px; object-fit:cover; border-radius:8px; border:1px solid #666; }
.book-badge { position:absolute; top:8px; right:8px; background:rgba(102,126,234,0.9); color:white; padding:2px 6px; border-radius:10px; font-size:10px; font-weight:bold;}
.book-info { flex-grow:1; display:flex; flex-direction:column; gap:4px; }
.book-title { font-size:13px; font-weight:700; color:#fff; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; }
.book-authors { font-size:11px; color:#88c; overflow:hidden; display:-webkit-box; -webkit-line-clamp:1; -webkit-box-orient:vertical;}
.book-rating { font-size:10px; color:#ffa500; }
.book-meta { display:flex; flex-direction:column; gap:2px; margin-top:auto; font-size:10px; color:#ccc; }
.description-scroll { max-height:150px; overflow-y:auto; padding-right:6px; margin-top:6px; border:1px solid #444; border-radius:6px; }

.load-more-btn { background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); color:white; border:none; padding:10px 25px; border-radius:20px; font-weight:600; cursor:pointer; transition:all 0.3s ease; font-size:12px; margin:5px; }
.load-more-btn:hover { transform:translateY(-2px); }

#card-details-popup { position:absolute; background:#111; color:#eee; padding:16px; border-radius:12px; box-shadow:0 10px 30px rgba(0,0,0,0.7); max-width:320px; z-index:9999; display:none; }
#card-details-popup-close { position:absolute; top:6px; right:8px; cursor:pointer; font-weight:bold; font-size:18px; }
""") as demo:

    gr.Markdown("# 📚 Dark Book Hub")
    gr.Markdown("### Explore curated books")

    # ---------- Random Section ----------
    gr.Markdown("## 🎲 Random Books")
    random_books_container = gr.HTML(elem_classes="books-section")
    random_load_more_btn = gr.Button("Load More Random", elem_classes="load-more-btn")

    # ---------- States ----------
    random_books_state = gr.State(df.sample(frac=1).reset_index(drop=True))
    random_display_state = gr.State(pd.DataFrame())
    random_index_state = gr.State(0)

    # ---------- Functions ----------
    def initial_load(df_):
        initial_books = df_.iloc[:BOOKS_PER_LOAD]
        html = build_books_grid_html(initial_books)
        return initial_books, html, 1

    def load_more(loaded, display, idx):
        start = idx*BOOKS_PER_LOAD
        end = start+BOOKS_PER_LOAD
        new_books = loaded.iloc[start:end]
        if new_books.empty:
            return display, gr.update(value=build_books_grid_html(display)), gr.update(visible=False), idx
        combined = pd.concat([display,new_books],ignore_index=True)
        html = build_books_grid_html(combined)
        return combined, gr.update(value=html), gr.update(visible=True), idx+1

    # ---------- Event Handlers ----------
    random_load_more_btn.click(load_more, [random_books_state, random_display_state, random_index_state],
                              [random_display_state, random_books_container, random_load_more_btn, random_index_state])

    # ---------- Initial Load ----------
    random_display_state.value, random_books_container.value, random_index_state.value = initial_load(random_books_state.value)

    # ---------- Details Popup ----------
    gr.HTML("""
    <div id="card-details-popup">
        <span id="card-details-popup-close">&times;</span>
        <div id="card-details-popup-content"></div>
    </div>

    <script>
    const popup = document.getElementById('card-details-popup');
    const content = document.getElementById('card-details-popup-content');
    const closeBtn = document.getElementById('card-details-popup-close');

    document.addEventListener('click', e => {
        const card = e.target.closest('.book-card');
        if(!card) return;

        // Populate popup
        content.innerHTML = `<h3>${card.dataset.title}</h3>
            <p><strong>Author(s):</strong> ${card.dataset.authors}</p>
            <p><strong>Genres:</strong> ${card.dataset.genres}</p>
            <p><strong>Rating:</strong> ${card.dataset.rating}</p>
            <p><strong>Year:</strong> ${card.dataset.year}</p>
            <p><strong>Pages:</strong> ${card.dataset.pages}</p>
            <div class="description-scroll">${card.dataset.desc}</div>`;

        // Position next to the card
        const rect = card.getBoundingClientRect();
        let top = window.scrollY + rect.top;
        let left = window.scrollX + rect.right + 10;
        if(left + 320 > window.innerWidth) left = window.scrollX + rect.left - 330;

        popup.style.top = top + 'px';
        popup.style.left = left + 'px';
        popup.style.display = 'block';
    });

    closeBtn.addEventListener('click', () => {
        popup.style.display = 'none';
    });

    document.addEventListener('keydown', e => {
        if(e.key === "Escape") popup.style.display = 'none';
    });

    document.addEventListener('click', e => {
        if(!e.target.closest('.book-card') && !e.target.closest('#card-details-popup')) {
            popup.style.display = 'none';
        }
    });
    </script>
    """)

demo.launch()
