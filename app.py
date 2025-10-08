import pandas as pd
import gradio as gr
import random
import ast

# ======= Load dataset =======
df = pd.read_csv("data_mini_books.csv")

# Ensure an 'id' column exists
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

# Convert stringified lists to actual lists
df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# Fill missing columns
df["rating"] = df.get("rating", [random.uniform(3.5, 4.8) for _ in range(len(df))])
df["year"] = df.get("year", [random.randint(1990, 2023) for _ in range(len(df))])
df["pages"] = df.get("pages", [random.randint(150, 600) for _ in range(len(df))])

BOOKS_PER_LOAD = 12
favorites_list = []

# ======= Helper Functions =======

def create_book_card_html(book, is_favorite=False):
    """Return HTML for a single book card."""
    rating = book.get("rating", 0)
    stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
    if rating % 1 >= 0.5:
        stars = "⭐" * (int(rating) + 1) + "☆" * (4 - int(rating))
    
    favorite_indicator = "❤️ " if is_favorite else ""
    
    return f"""
    <div class='book-card' data-id='{book["id"]}' data-title="{book['title']}" 
         data-authors="{', '.join(book['authors'])}" data-genres="{', '.join(book['genres'])}" 
         data-img="{book['image_url']}" data-desc="{book.get('description', 'No description')}"
         data-rating="{rating}" data-year="{book.get('year', 'N/A')}" data-pages="{book.get('pages', 'N/A')}">
        <div class='book-image-container'>
            <img src="{book['image_url']}" onerror="this.src='https://via.placeholder.com/150x220/444/fff?text=No+Image'">
            <div class='book-badge'>{book.get('year', 'N/A')}</div>
        </div>
        <div class='book-info'>
            <div class='book-title' title="{book['title']}">{favorite_indicator}{book['title']}</div>
            <div class='book-authors'>by {', '.join(book['authors'])}</div>
            <div class='book-rating'>{stars} ({rating:.1f})</div>
            <div class='book-meta'>
                <span class='book-pages'>{book.get('pages', 'N/A')} pages</span>
                <span class='book-genres'>{', '.join(book['genres'][:2])}{'...' if len(book['genres'])>2 else ''}</span>
            </div>
        </div>
    </div>
    """


def build_books_grid_html(books_df, is_favorites_section=False):
    """Builds the grid HTML for multiple books."""
    if books_df.empty:
        if is_favorites_section:
            return "<div style='text-align:center; padding:40px; color:#888;'>No favorite books yet.</div>"
        return "<div style='text-align:center; padding:40px; color:#888;'>No books found.</div>"
    
    cards_html = []
    for _, book in books_df.iterrows():
        is_fav = is_favorites_section or any(fav['id'] == book['id'] for fav in favorites_list)
        cards_html.append(create_book_card_html(book, is_fav))
    
    return f"<div class='books-grid'>{''.join(cards_html)}</div>"


def add_to_favorites(book_id):
    """Add a book to favorites."""
    global favorites_list
    book_match = df[df['id'] == book_id]
    if not book_match.empty:
        book_data = book_match.iloc[0].to_dict()
        if not any(fav['id'] == book_id for fav in favorites_list):
            favorites_list.append(book_data)
            return True, f"❤️ Added '{book_data['title']}' to favorites!"
        else:
            return False, "⚠️ Already in favorites!"
    return False, "❌ Book not found!"


def update_favorites_display():
    """Return updated favorites HTML and count."""
    favorites_df = pd.DataFrame(favorites_list)
    html = build_books_grid_html(favorites_df, is_favorites_section=True)
    count_html = f"<h3>⭐ Favorites ({len(favorites_list)} books)</h3>"
    return favorites_df, html, count_html


# ======= Gradio UI =======
with gr.Blocks() as demo:
    
    gr.Markdown("# 📚 Dark Book Discovery Hub")
    gr.Markdown("Explore our curated collection of amazing books")
    
    # Random Books Section
    gr.Markdown("## 🎲 Random Books")
    random_books_container = gr.HTML(elem_classes="books-section")
    
    random_books_state = gr.State(df.sample(frac=1).reset_index(drop=True))
    random_display_state = gr.State(pd.DataFrame())
    random_index_state = gr.State(0)
    
    def load_random(loaded_books, display_books, page_idx):
        start = page_idx * BOOKS_PER_LOAD
        end = start + BOOKS_PER_LOAD
        new_books = loaded_books.iloc[start:end]
        if new_books.empty:
            return display_books, gr.update(value=build_books_grid_html(display_books)), page_idx
        combined = pd.concat([display_books, new_books], ignore_index=True)
        html = build_books_grid_html(combined)
        return combined, gr.update(value=html), page_idx + 1
    
    random_load_more_btn = gr.Button("📚 Load More Random Books")
    random_load_more_btn.click(
        load_random,
        [random_books_state, random_display_state, random_index_state],
        [random_display_state, random_books_container, random_index_state]
    )
    
    # Favorites Section
    gr.Markdown("## ⭐ Favorites")
    favorites_container = gr.HTML(
        "<div style='text-align:center; padding:40px; color:#888;'>No favorite books yet.</div>"
    )
    favorites_state = gr.State(pd.DataFrame())
    
    def handle_add_favorite(book_id):
        added, msg = add_to_favorites(book_id)
        favorites_df, html, count_html = update_favorites_display()
        return favorites_df, gr.update(value=html), count_html, msg
    
    # Hidden trigger for JS
    add_fav_trigger = gr.Button("Add Favorite Simple", visible=False)
    add_fav_book_id = gr.Textbox(value="", visible=False)
    add_fav_trigger.click(
        handle_add_favorite,
        inputs=[add_fav_book_id],
        outputs=[favorites_state, favorites_container, favorites_container, gr.Textbox()]
    )
    
    # Initial load
    def initial_load(df_):
        initial_books = df_.iloc[:BOOKS_PER_LOAD]
        html = build_books_grid_html(initial_books)
        return initial_books, gr.update(value=html), 1
    
    random_display_state.value, random_books_container.value, random_index_state.value = initial_load(random_books_state.value)
    
    # ======= CSS =======
    gr.HTML("""
    <style>
    .books-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:16px; }
    .book-card { background:#333; color:#eee; padding:8px; border-radius:10px; cursor:pointer; }
    .book-card img { width:100%; height:180px; object-fit:cover; border-radius:6px; }
    .book-info { padding:5px; }
    </style>
    """)
    
    # ======= JS Popup =======
    gr.HTML("""
    <div id="popup-overlay" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:1000;"></div>
    <div id="popup-container" style="display:none; position:fixed; top:50%; left:50%; transform:translate(-50%,-50%);
        background:#111; padding:20px; border-radius:12px; max-width:600px; max-height:80vh; overflow-y:auto; color:#eee; z-index:1001;">
        <span id="popup-close" style="position:absolute;top:10px;right:15px;cursor:pointer;font-size:20px;">&times;</span>
        <div id="popup-content"></div>
    </div>
    
    <script>
    const overlay = document.getElementById('popup-overlay');
    const container = document.getElementById('popup-container');
    const closeBtn = document.getElementById('popup-close');
    const content = document.getElementById('popup-content');

    document.addEventListener('click', function(e){
        const card = e.target.closest('.book-card');
        if(!card) return;
        const title = card.dataset.title;
        const authors = card.dataset.authors;
        const genres = card.dataset.genres;
        const desc = card.dataset.desc;
        const img = card.dataset.img;
        const rating = card.dataset.rating;
        const pages = card.dataset.pages;
        const year = card.dataset.year;
        const bookId = card.dataset.id;

        content.innerHTML = `
            <img src="${img}" style="width:150px; float:left; margin-right:15px;">
            <h2>${title}</h2>
            <p><strong>Author(s):</strong> ${authors}</p>
            <p><strong>Genres:</strong> ${genres}</p>
            <p><strong>Rating:</strong> ${rating}</p>
            <p><strong>Pages:</strong> ${pages}</p>
            <p><strong>Year:</strong> ${year}</p>
            <p>${desc}</p>
            <button onclick="document.querySelector('input[type=text]').value='${bookId}'; 
                document.querySelector('button:contains(Add Favorite Simple)').click(); 
                overlay.style.display='none'; container.style.display='none';">
                ❤️ Add to Favorites
            </button>
        `;
        overlay.style.display='block';
        container.style.display='block';
    });

    closeBtn.onclick = overlay.onclick = () => {
        overlay.style.display='none';
        container.style.display='none';
    };
    </script>
    """)

demo.launch()
