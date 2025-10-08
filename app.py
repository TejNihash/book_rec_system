# @title
import ast
import pandas as pd
import gradio as gr
import random
import json

# ---------- Load dataset ----------
df = pd.read_csv("data_mini_books.csv")
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# Add additional book metrics
df["rating"] = df.get("rating", [random.uniform(3.5, 4.8) for _ in range(len(df))])
df["year"] = df.get("year", [random.randint(1990, 2023) for _ in range(len(df))])
df["pages"] = df.get("pages", [random.randint(150, 600) for _ in range(len(df))])

BOOKS_PER_LOAD = 12  # 2 rows × 6 columns

# ---------- Favorites Management ----------
favorites_state = gr.State([])  # Global state for favorites

def add_to_favorites(book_id, current_favorites, books_df):
    """Add a book to favorites if not already present"""
    book_data = books_df[books_df["id"] == book_id].iloc[0]
    book_dict = {
        "id": book_data["id"],
        "title": book_data["title"],
        "authors": book_data["authors"],
        "image_url": book_data["image_url"],
        "rating": book_data.get("rating", 0),
        "year": book_data.get("year", "N/A")
    }
    
    # Check if already in favorites
    if book_id not in [fav["id"] for fav in current_favorites]:
        updated_favorites = current_favorites + [book_dict]
        return updated_favorites, build_favorites_html(updated_favorites)
    return current_favorites, build_favorites_html(current_favorites)

def remove_from_favorites(book_id, current_favorites):
    """Remove a book from favorites"""
    updated_favorites = [fav for fav in current_favorites if fav["id"] != book_id]
    return updated_favorites, build_favorites_html(updated_favorites)

def build_favorites_html(favorites):
    """Build HTML for favorites sidebar"""
    if not favorites:
        return """
        <div class="favorites-empty">
            <div style="text-align: center; padding: 40px 20px; color: #666;">
                <div style="font-size: 48px; margin-bottom: 16px;">📚</div>
                <h3 style="margin: 0 0 8px 0; color: #444;">No favorites yet</h3>
                <p style="margin: 0; font-size: 14px;">Click the heart button on any book to add it here!</p>
            </div>
        </div>
        """
    
    favorites_html = []
    for fav in favorites:
        stars = "⭐" * int(fav["rating"]) + "☆" * (5 - int(fav["rating"]))
        if fav["rating"] % 1 >= 0.5:
            stars = "⭐" * (int(fav["rating"]) + 1) + "☆" * (4 - int(fav["rating"]))
        
        authors_str = ', '.join(fav["authors"]) if isinstance(fav["authors"], list) else fav["authors"]
        
        favorites_html.append(f"""
        <div class="favorite-item" data-id="{fav['id']}">
            <div class="favorite-image">
                <img src="{fav['image_url']}" onerror="this.src='https://via.placeholder.com/60x80/667eea/white?text=No+Image'">
            </div>
            <div class="favorite-info">
                <div class="favorite-title" title="{fav['title']}">{fav['title']}</div>
                <div class="favorite-authors">{authors_str}</div>
                <div class="favorite-rating">{stars}</div>
                <div class="favorite-year">{fav.get('year', 'N/A')}</div>
            </div>
            <button class="favorite-remove-btn" onclick="removeFavorite('{fav['id']}')">×</button>
        </div>
        """)
    
    return f'<div class="favorites-list">{""".join(favorites_html)}</div>'

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
            <button class='favorite-add-btn' onclick="addFavorite('{book["id"]}')">♡</button>
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
/* Main layout with favorites sidebar */
.app-container {
    display: flex;
    gap: 20px;
    max-width: 100%;
}
.main-content {
    flex: 1;
    min-width: 0;
}
.favorites-sidebar {
    width: 320px;
    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
    border-radius: 12px;
    padding: 20px;
    border: 1px solid #e0e0e0;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    height: fit-content;
    max-height: 80vh;
    position: sticky;
    top: 20px;
}
.favorites-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 2px solid #667eea;
}
.favorites-title {
    font-size: 18px;
    font-weight: bold;
    color: #2d3748;
    margin: 0;
}
.favorites-count {
    background: #667eea;
    color: white;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: bold;
}
.favorites-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
    max-height: 70vh;
    overflow-y: auto;
}
.favorite-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px;
    background: white;
    border-radius: 8px;
    border: 1px solid #eaeaea;
    transition: all 0.3s ease;
    position: relative;
}
.favorite-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    border-color: #667eea;
}
.favorite-image {
    flex-shrink: 0;
}
.favorite-image img {
    width: 60px;
    height: 80px;
    object-fit: cover;
    border-radius: 4px;
    border: 1px solid #eee;
}
.favorite-info {
    flex: 1;
    min-width: 0;
}
.favorite-title {
    font-size: 13px;
    font-weight: bold;
    color: #222;
    margin-bottom: 4px;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
}
.favorite-authors {
    font-size: 11px;
    color: #667eea;
    font-weight: 600;
    margin-bottom: 3px;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
}
.favorite-rating {
    font-size: 10px;
    color: #ffa500;
    margin-bottom: 2px;
}
.favorite-year {
    font-size: 10px;
    color: #666;
    font-weight: 500;
}
.favorite-remove-btn {
    position: absolute;
    top: 8px;
    right: 8px;
    background: #dc3545;
    color: white;
    border: none;
    border-radius: 50%;
    width: 20px;
    height: 20px;
    cursor: pointer;
    font-size: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
}
.favorite-remove-btn:hover {
    background: #c82333;
    transform: scale(1.1);
}
.favorites-empty {
    text-align: center;
    padding: 40px 20px;
    color: #666;
}

/* Favorite button on book cards */
.favorite-add-btn {
    position: absolute;
    top: 8px;
    left: 8px;
    background: rgba(255, 255, 255, 0.9);
    border: none;
    border-radius: 50%;
    width: 32px;
    height: 32px;
    cursor: pointer;
    font-size: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
    box-shadow: 0 2px 6px rgba(0,0,0,0.2);
}
.favorite-add-btn:hover {
    background: #ff6b6b;
    color: white;
    transform: scale(1.1);
}
.favorite-add-btn.favorited {
    background: #ff6b6b;
    color: white;
}

/* Existing styles remain the same */
.books-section {
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 16px;
    height: 500px;
    overflow-y: auto;
    margin-bottom: 20px;
    background: linear-gradient(135deg, #f7f7f7 0%, #ffffff 100%);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.books-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 16px;
}
.book-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 10px;
    box-shadow: 0 3px 10px rgba(0,0,0,0.15);
    cursor: pointer;
    text-align: left;
    transition: all 0.3s ease;
    border: 1px solid #eaeaea;
    height: 100%;
    display: flex;
    flex-direction: column;
    position: relative;
}
.book-card:hover {
    transform: translateY(-4px) scale(1.02);
    box-shadow: 0 8px 20px rgba(0,0,0,0.25);
    border-color: #667eea;
}
.book-image-container {
    position: relative;
    margin-bottom: 10px;
}
.book-card img {
    width: 100%;
    height: 180px;
    object-fit: cover;
    border-radius: 8px;
    border: 1px solid #eee;
}
.book-badge {
    position: absolute;
    top: 8px;
    right: 8px;
    background: rgba(102, 126, 234, 0.9);
    color: white;
    padding: 2px 6px;
    border-radius: 10px;
    font-size: 10px;
    font-weight: bold;
}
.book-info {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.book-title { 
    font-size: 13px; 
    font-weight: 700; 
    color: #222; 
    line-height: 1.3;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    margin-bottom: 2px;
}
.book-authors { 
    font-size: 11px; 
    color: #667eea; 
    font-weight: 600;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
    margin-bottom: 3px;
}
.book-rating {
    font-size: 10px;
    color: #ffa500;
    margin-bottom: 4px;
}
.book-meta {
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin-top: auto;
}
.book-pages {
    font-size: 10px;
    color: #666;
    font-weight: 500;
}
.book-genres {
    font-size: 9px;
    color: #888;
    font-style: italic;
}
.load-more-section {
    text-align: center;
    margin: 10px 0;
}
.load-more-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 10px 25px;
    border-radius: 20px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    font-size: 12px;
}
.load-more-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}
.section-title {
    font-size: 20px;
    font-weight: bold;
    color: #2d3748;
    margin-bottom: 15px;
    border-left: 4px solid #667eea;
    padding-left: 12px;
}

/* Popup styles remain the same */
#popup-overlay, #popup-container {
    position: fixed !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
    z-index: 9999 !important;
}
#popup-overlay {
    width: 100vw;
    height: 100vh;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(5px);
    display: none;
}
#popup-container {
    max-width: 700px;
    width: 90%;
    max-height: 80vh;
    overflow-y: auto;
    background: #fff;
    border-radius: 16px;
    padding: 24px;
    display: none;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    border: 2px solid #667eea;
}
.popup-close {
    position: absolute;
    top: 12px;
    right: 16px;
    cursor: pointer;
    font-size: 24px;
    font-weight: bold;
    color: #222;
    background: #f0f0f0;
    border-radius: 50%;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    transition: all 0.2s ease;
}
.popup-close:hover {
    background: #667eea;
    color: white;
}
.popup-content {
    line-height: 1.6;
    font-size: 15px;
    color: #222;
}
.detail-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin: 15px 0;
    padding: 12px;
    background: #f0f4ff;
    border-radius: 8px;
    border: 1px solid #d0d6ff;
}
.detail-stat {
    text-align: center;
}
.detail-stat-value {
    font-size: 16px;
    font-weight: bold;
    color: #667eea;
}
.detail-stat-label {
    font-size: 11px;
    color: #444;
    margin-top: 2px;
}
.description-scroll {
    max-height: 200px;
    overflow-y: auto;
    padding-right: 8px;
    margin-top: 10px;
}
.description-scroll::-webkit-scrollbar {
    width: 6px;
}
.description-scroll::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 3px;
}
.description-scroll::-webkit-scrollbar-thumb {
    background: #667eea;
    border-radius: 3px;
}
.description-scroll::-webkit-scrollbar-thumb:hover {
    background: #5a6fd8;
}
""") as demo:

    gr.HTML("""
    <div class="popup-overlay" id="popup-overlay"></div>
    <div class="popup-container" id="popup-container">
        <span class="popup-close" id="popup-close">&times;</span>
        <div class="popup-content" id="popup-content"></div>
    </div>
    """, elem_id="popup-top-level")

    gr.Markdown("# 📚 Book Discovery Hub")
    gr.Markdown("### Explore our curated collection of amazing books")

    # Main app container with favorites sidebar
    with gr.Row(elem_classes="app-container"):
        # Main content area
        with gr.Column(elem_classes="main-content"):
            # === RANDOM BOOKS SECTION ===  
            gr.Markdown("## 🎲 Random Books")
            with gr.Column():
                random_books_container = gr.HTML(elem_classes="books-section")
                
                with gr.Row():
                    random_load_more_btn = gr.Button("📚 Load More Random Books", elem_classes="load-more-btn")
                    shuffle_btn = gr.Button("🔀 Shuffle Books", elem_classes="load-more-btn")

            # === POPULAR BOOKS SECTION ===
            gr.Markdown("## 📈 Popular Books")
            with gr.Column():
                popular_books_container = gr.HTML(elem_classes="books-section")
                
                with gr.Row():
                    popular_load_more_btn = gr.Button("📚 Load More Popular Books", elem_classes="load-more-btn")

        # Favorites sidebar
        with gr.Column(elem_classes="favorites-sidebar"):
            with gr.Column():
                gr.HTML("""
                <div class="favorites-header">
                    <h2 class="favorites-title">❤️ Favorites</h2>
                    <div class="favorites-count" id="favorites-count">0</div>
                </div>
                """)
                favorites_container = gr.HTML(build_favorites_html([]))

    # State management
    random_books_state = gr.State(df.sample(frac=1).reset_index(drop=True))
    random_display_state = gr.State(pd.DataFrame())
    random_index_state = gr.State(0)
    
    popular_books_state = gr.State(df.copy())
    popular_display_state = gr.State(pd.DataFrame())
    popular_index_state = gr.State(0)
    
    favorites_state = gr.State([])

    # ---------- Functions ----------
    def load_more_random(loaded_books, display_books, page_idx):
        start = page_idx * BOOKS_PER_LOAD
        end = start + BOOKS_PER_LOAD
        new_books = loaded_books.iloc[start:end]
        if new_books.empty:
            return display_books, gr.update(value=build_books_grid_html(display_books)), gr.update(visible=False), page_idx
        combined = pd.concat([display_books, new_books], ignore_index=True)
        html = build_books_grid_html(combined)
        return combined, gr.update(value=html), gr.update(visible=True), page_idx + 1

    def load_more_popular(loaded_books, display_books, page_idx):
        start = page_idx * BOOKS_PER_LOAD
        end = start + BOOKS_PER_LOAD
        new_books = loaded_books.iloc[start:end]
        if new_books.empty:
            return display_books, gr.update(value=build_books_grid_html(display_books)), gr.update(visible=False), page_idx
        combined = pd.concat([display_books, new_books], ignore_index=True)
        html = build_books_grid_html(combined)
        return combined, gr.update(value=html), gr.update(visible=True), page_idx + 1

    def shuffle_random_books(loaded_books, display_books):
        shuffled = loaded_books.sample(frac=1).reset_index(drop=True)
        initial_books = shuffled.iloc[:BOOKS_PER_LOAD]
        html = build_books_grid_html(initial_books)
        return shuffled, initial_books, html, 1

    # Event handlers
    random_load_more_btn.click(
        load_more_random,
        [random_books_state, random_display_state, random_index_state],
        [random_display_state, random_books_container, random_load_more_btn, random_index_state]
    )

    shuffle_btn.click(
        shuffle_random_books,
        [random_books_state, random_display_state],
        [random_books_state, random_display_state, random_books_container, random_index_state]
    )

    popular_load_more_btn.click(
        load_more_popular,
        [popular_books_state, popular_display_state, popular_index_state],
        [popular_display_state, popular_books_container, popular_load_more_btn, popular_index_state]
    )

    # Initialize sections
    def initial_load_random(loaded_books):
        initial_books = loaded_books.iloc[:BOOKS_PER_LOAD]
        html = build_books_grid_html(initial_books)
        return initial_books, html, 1

    def initial_load_popular(loaded_books):
        initial_books = loaded_books.iloc[:BOOKS_PER_LOAD]
        html = build_books_grid_html(initial_books)
        return initial_books, html, 1

    # Set initial values
    random_display_state.value, random_books_container.value, random_index_state.value = initial_load_random(random_books_state.value)
    popular_display_state.value, popular_books_container.value, popular_index_state.value = initial_load_popular(popular_books_state.value)

    # ---------- JavaScript for Favorites Management ----------
    gr.HTML(f"""
    <script>
    const dfData = {df.to_json(orient='records')};
    
    function updateFavoritesCount() {{
        const favorites = JSON.parse(localStorage.getItem('bookFavorites') || '[]');
        document.getElementById('favorites-count').textContent = favorites.length;
        return favorites.length;
    }}
    
    function addFavorite(bookId) {{
        const favorites = JSON.parse(localStorage.getItem('bookFavorites') || '[]');
        const bookData = dfData.find(book => book.id == bookId);
        
        if (bookData && !favorites.find(fav => fav.id == bookId)) {{
            const bookToAdd = {{
                id: bookData.id,
                title: bookData.title,
                authors: bookData.authors,
                image_url: bookData.image_url,
                rating: bookData.rating || 0,
                year: bookData.year || 'N/A'
            }};
            favorites.push(bookToAdd);
            localStorage.setItem('bookFavorites', JSON.stringify(favorites));
            updateFavoritesCount();
            
            // Update button appearance
            const btn = event.target;
            btn.textContent = '❤';
            btn.classList.add('favorited');
            
            // Trigger Gradio update
            gradioApp().querySelector('#favorites-container').dispatchEvent(new Event('change'));
        }}
    }}
    
    function removeFavorite(bookId) {{
        let favorites = JSON.parse(localStorage.getItem('bookFavorites') || '[]');
        favorites = favorites.filter(fav => fav.id != bookId);
        localStorage.setItem('bookFavorites', JSON.stringify(favorites));
        updateFavoritesCount();
        
        // Trigger Gradio update
        gradioApp().querySelector('#favorites-container').dispatchEvent(new Event('change'));
    }}
    
    // Initialize favorites count
    document.addEventListener('DOMContentLoaded', function() {{
        updateFavoritesCount();
    }});
    
    // Existing popup JavaScript remains the same
    const overlay = document.getElementById('popup-overlay');
    const container = document.getElementById('popup-container');
    const closeBtn = document.getElementById('popup-close');
    const content = document.getElementById('popup-content');
    
    let originalScrollPosition = 0;
    
    function escapeHtml(str) {{
        return str ? String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;') : "";
    }}
    
    function formatText(text) {{
        if (!text) return 'No description available.';
        return text.replace(/\\n/g, '<br>');
    }}
    
    function calculateSmartPosition() {{
        const viewportHeight = window.innerHeight;
        const viewportWidth = window.innerWidth;
        const popupHeight = container.offsetHeight;
        const popupWidth = container.offsetWidth;
        
        const scrollY = window.scrollY;
        
        const availableTopSpace = scrollY;
        const availableBottomSpace = document.documentElement.scrollHeight - (scrollY + viewportHeight);
        
        let topPosition = scrollY + (viewportHeight / 2) - (popupHeight / 2);
        
        const minTop = scrollY + 20;
        const maxTop = scrollY + viewportHeight - popupHeight - 20;
            
        if (topPosition < minTop) {{
            topPosition = minTop;
        }} else if (topPosition > maxTop) {{
            topPosition = maxTop;
        }}
        
        const leftPosition = (viewportWidth / 2) - (popupWidth / 2);
        
        return {{ top: topPosition, left: leftPosition }};
    }}
    
    function showPopup() {{
        originalScrollPosition = window.scrollY || document.documentElement.scrollTop;
        
        overlay.style.display = 'block';
        container.style.display = 'block';
        
        const position = calculateSmartPosition();
        container.style.position = 'absolute';
        container.style.top = position.top + 'px';
        container.style.left = position.left + 'px';
        container.style.transform = 'none';
        
        document.body.style.overflow = 'hidden';
    }}
    
    function closePopup() {{
        overlay.style.display = 'none';
        container.style.display = 'none';
        document.body.style.overflow = 'auto';
        window.scrollTo(0, originalScrollPosition);
    }}
    
    document.addEventListener('click', function(e) {{
        const card = e.target.closest('.book-card');
        if (!card) return;
        
        if (e.target.classList.contains('favorite-add-btn')) {{
            return; // Don't show popup when clicking favorite button
        }}
        
        const title = card.dataset.title;
        const authors = card.dataset.authors;
        const genres = card.dataset.genres;
        const desc = card.dataset.desc;
        const img = card.dataset.img;
        const rating = card.dataset.rating || '0';
        const year = card.dataset.year || 'N/A';
        const pages = card.dataset.pages || 'N/A';
        
        const numRating = parseFloat(rating);
        const fullStars = Math.floor(numRating);
        const hasHalfStar = numRating % 1 >= 0.5;
        let stars = '⭐'.repeat(fullStars);
        if (hasHalfStar) stars += '½';
        stars += '☆'.repeat(5 - fullStars - (hasHalfStar ? 1 : 0));
        
        content.innerHTML = `
            <div style="display: flex; gap: 20px; align-items: flex-start; margin-bottom: 20px;">
                <img src="${{img}}" style="width: 180px; height: auto; border-radius: 8px; object-fit: cover; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
                <div style="flex: 1; color: #222;">
                    <h2 style="margin: 0 0 12px 0; color: #1a202c; border-bottom: 2px solid #667eea; padding-bottom: 8px;">${{escapeHtml(title)}}</h2>
                    <p style="margin: 0 0 8px 0; font-size: 15px;"><strong>Author(s):</strong> <span style="color: #667eea;">${{escapeHtml(authors)}}</span></p>
                    <p style="margin: 0 0 8px 0; font-size: 15px;"><strong>Genres:</strong> <span style="color: #764ba2;">${{escapeHtml(genres)}}</span></p>
                    <p style="margin: 0 0 8px 0; font-size: 15px;"><strong>Rating:</strong> ${{stars}} <strong style="color: #667eea;">${{parseFloat(rating).toFixed(1)}}</strong></p>
                </div>
            </div>
            <div class="detail-stats">
                <div class="detail-stat">
                    <div class="detail-stat-value">${{escapeHtml(year)}}</div>
                    <div class="detail-stat-label">PUBLICATION YEAR</div>
                </div>
                <div class="detail-stat">
                    <div class="detail-stat-value">${{escapeHtml(pages)}}</div>
                    <div class="detail-stat-label">PAGES</div>
                </div>
                <div class="detail-stat">
                    <div class="detail-stat-value">${{Math.ceil(parseInt(pages) / 250) || 'N/A'}}</div>
                    <div class="detail-stat-label">READING TIME (HOURS)</div>
                </div>
            </div>
            <div style="margin-top: 15px;">
                <h3 style="margin: 0 0 10px 0; color: #1a202c; font-size: 16px;">Description</h3>
                <div class="description-scroll">
                    ${{formatText(escapeHtml(desc))}}
                </div>
            </div>
            `;
        
        showPopup();
    }});
    
    closeBtn.addEventListener('click', closePopup);
    overlay.addEventListener('click', closePopup);
    
    document.addEventListener('keydown', function(e) {{
        if (e.key === 'Escape') {{
            closePopup();
        }}
    }});
    
    container.addEventListener('click', function(e) {{
        e.stopPropagation();
    }});
    
    window.addEventListener('resize', function() {{
        if (container.style.display === 'block') {{
            const position = calculateSmartPosition();
            container.style.top = position.top + 'px';
            container.style.left = position.left + 'px';
        }}
    }});
    </script>
    """)

demo.launch()