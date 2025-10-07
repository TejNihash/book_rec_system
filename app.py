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
    if books_df.empty:
        return "<div style='text-align: center; padding: 40px; color: #666;'>No books found</div>"
    cards_html = [create_book_card_html(book) for _, book in books_df.iterrows()]
    return f"<div class='books-grid'>{''.join(cards_html)}</div>"

def search_books(search_query, current_random_books, current_display_books):
    """Search books by title, author, or genre"""
    if not search_query.strip():
        return current_random_books.iloc[:BOOKS_PER_LOAD], gr.update(value=build_books_grid_html(current_random_books.iloc[:BOOKS_PER_LOAD]), visible=True), gr.update(visible=True), gr.update(visible=False)
    
    search_lower = search_query.lower()
    
    mask = (
        df['title'].str.lower().str.contains(search_lower, na=False) |
        df['authors'].apply(lambda authors: any(search_lower in author.lower() for author in authors)) |
        df['genres'].apply(lambda genres: any(search_lower in genre.lower() for genre in genres))
    )
    
    search_results = df[mask].reset_index(drop=True)
    
    if search_results.empty:
        return pd.DataFrame(), gr.update(value="<div style='text-align: center; padding: 40px; color: #666;'>No books found matching your search</div>", visible=True), gr.update(visible=False), gr.update(visible=True)
    
    return search_results, gr.update(value=build_books_grid_html(search_results), visible=True), gr.update(visible=False), gr.update(visible=True)

def clear_search(current_random_books):
    """Clear search and show random books"""
    initial_books = current_random_books.iloc[:BOOKS_PER_LOAD]
    return gr.update(value=""), initial_books, gr.update(value=build_books_grid_html(initial_books)), gr.update(visible=True), gr.update(visible=False)

# ---------- Favorites Functions ----------
def get_favorites():
    """Get favorites from storage"""
    try:
        return gr.State(value=pd.DataFrame())
    except:
        return gr.State(value=pd.DataFrame())

def add_to_favorites(book_id, favorites_df, favorites_display):
    """Add book to favorites"""
    book = df[df['id'] == book_id].iloc[0]
    
    if favorites_df.empty:
        favorites_df = pd.DataFrame([book])
    else:
        if book_id not in favorites_df['id'].values:
            favorites_df = pd.concat([favorites_df, pd.DataFrame([book])], ignore_index=True)
    
    # Update display with current favorites
    current_display = favorites_df.iloc[:len(favorites_display) + BOOKS_PER_LOAD] if not favorites_display.empty else favorites_df.iloc[:BOOKS_PER_LOAD]
    html = build_books_grid_html(current_display)
    
    return favorites_df, current_display, gr.update(value=html), gr.update(visible=len(favorites_df) > len(current_display))

def remove_from_favorites(book_id, favorites_df, favorites_display):
    """Remove book from favorites"""
    favorites_df = favorites_df[favorites_df['id'] != book_id].reset_index(drop=True)
    
    # Update display
    current_display = favorites_df.iloc[:len(favorites_display)] if len(favorites_display) <= len(favorites_df) else favorites_df.iloc[:BOOKS_PER_LOAD]
    html = build_books_grid_html(current_display)
    
    return favorites_df, current_display, gr.update(value=html), gr.update(visible=len(favorites_df) > len(current_display))

def load_more_favorites(favorites_df, favorites_display, page_idx):
    """Load more favorites"""
    start = page_idx * BOOKS_PER_LOAD
    end = start + BOOKS_PER_LOAD
    new_books = favorites_df.iloc[start:end]
    
    if new_books.empty:
        return favorites_display, gr.update(value=build_books_grid_html(favorites_display)), gr.update(visible=False), page_idx
    
    combined = pd.concat([favorites_display, new_books], ignore_index=True)
    html = build_books_grid_html(combined)
    return combined, gr.update(value=html), gr.update(visible=True), page_idx + 1

# ---------- Gradio UI ----------
with gr.Blocks(css="""
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
.favorite-btn {
    background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 20px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(237, 137, 54, 0.3);
    margin-top: 10px;
}
.favorite-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(237, 137, 54, 0.4);
}
.remove-favorite-btn {
    background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 20px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(245, 101, 101, 0.3);
    margin-top: 10px;
}
.remove-favorite-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(245, 101, 101, 0.4);
}
.search-btn {
    background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 20px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(72, 187, 120, 0.3);
}
.search-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(72, 187, 120, 0.4);
}
.clear-btn {
    background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 20px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(245, 101, 101, 0.3);
}
.clear-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(245, 101, 101, 0.4);
}
.search-section {
    background: linear-gradient(135deg, #edf2f7 0%, #f7fafc 100%);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    border: 1px solid #e2e8f0;
}
.search-header {
    font-size: 18px;
    font-weight: bold;
    color: #2d3748;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.search-results-indicator {
    background: #667eea;
    color: white;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    margin-left: auto;
}
.section-title {
    font-size: 20px;
    font-weight: bold;
    color: #2d3748;
    margin-bottom: 15px;
    border-left: 4px solid #667eea;
    padding-left: 12px;
}
.favorites-count {
    background: #ed8936;
    color: white;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    margin-left: 10px;
}

/* Popup Styles */
.popup-overlay {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(5px);
    z-index: 1000;
}
.popup-container {
    display: none;
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: #ffffff;
    border-radius: 16px;
    padding: 24px;
    max-width: 700px;
    width: 90%;
    max-height: 80vh;
    overflow-y: auto;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    border: 2px solid #667eea;
    z-index: 1001;
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
.favorite-action-section {
    margin-top: 20px;
    padding-top: 15px;
    border-top: 2px solid #ed8936;
    text-align: center;
}
""") as demo:

    gr.Markdown("# 📚 Book Discovery Hub")
    gr.Markdown("### Explore our curated collection of amazing books")

    # === SEARCH SECTION ===
    with gr.Column(elem_classes="search-section"):
        gr.Markdown("### 🔍 Search Books")
        with gr.Row():
            search_input = gr.Textbox(
                placeholder="Search by title, author, or genre...",
                show_label=False,
                container=False,
                scale=4
            )
            search_btn = gr.Button("🔍 Search", elem_classes="search-btn")
            clear_btn = gr.Button("🗑️ Clear", elem_classes="clear-btn", visible=False)
        
        search_indicator = gr.HTML(visible=False)

    # === RANDOM BOOKS SECTION ===  
    gr.Markdown("## 🎲 Books")
    with gr.Column():
        random_books_container = gr.HTML(elem_classes="books-section")
        
        with gr.Row():
            load_more_btn = gr.Button("📚 Load More Books", elem_classes="load-more-btn")
            shuffle_btn = gr.Button("🔀 Shuffle Books", elem_classes="load-more-btn")

    # === FAVORITES SECTION ===
    with gr.Column():
        favorites_header = gr.HTML("""
        <div style="display: flex; align-items: center; margin-bottom: 15px;">
            <h2 style="margin: 0; color: #2d3748; border-left: 4px solid #ed8936; padding-left: 12px;">⭐ Favorites</h2>
            <div class="favorites-count" id="favorites-count">0 books</div>
        </div>
        """)
        
        favorites_container = gr.HTML(elem_classes="books-section", value="<div style='text-align: center; padding: 40px; color: #666;'>No favorite books yet. Click the ❤️ button in book details to add some!</div>")
        
        with gr.Row():
            favorites_load_more_btn = gr.Button("📚 Load More Favorites", elem_classes="load-more-btn", visible=False)

    # === POPULAR BOOKS SECTION ===
    gr.Markdown("## 📈 Popular Books")
    with gr.Column():
        popular_books_container = gr.HTML(elem_classes="books-section")
        
        with gr.Row():
            popular_load_more_btn = gr.Button("📚 Load More Popular Books", elem_classes="load-more-btn")

    # State for all sections
    random_books_state = gr.State(df.sample(frac=1).reset_index(drop=True))
    random_display_state = gr.State(pd.DataFrame())
    random_index_state = gr.State(0)
    
    popular_books_state = gr.State(df.copy())
    popular_display_state = gr.State(pd.DataFrame())
    popular_index_state = gr.State(0)
    
    # Favorites state
    favorites_state = gr.State(pd.DataFrame())
    favorites_display_state = gr.State(pd.DataFrame())
    favorites_index_state = gr.State(0)

    # Search state
    is_searching_state = gr.State(False)
    search_results_state = gr.State(pd.DataFrame())

    # ---------- Functions ----------
    def load_more_random(loaded_books, display_books, page_idx, is_searching, search_results):
        if is_searching:
            start = page_idx * BOOKS_PER_LOAD
            end = start + BOOKS_PER_LOAD
            new_books = search_results.iloc[start:end]
            if new_books.empty:
                return display_books, gr.update(value=build_books_grid_html(display_books)), gr.update(visible=False), page_idx, is_searching, search_results
            combined = pd.concat([display_books, new_books], ignore_index=True)
            html = build_books_grid_html(combined)
            return combined, gr.update(value=html), gr.update(visible=True), page_idx + 1, is_searching, search_results
        else:
            start = page_idx * BOOKS_PER_LOAD
            end = start + BOOKS_PER_LOAD
            new_books = loaded_books.iloc[start:end]
            if new_books.empty:
                return display_books, gr.update(value=build_books_grid_html(display_books)), gr.update(visible=False), page_idx, is_searching, search_results
            combined = pd.concat([display_books, new_books], ignore_index=True)
            html = build_books_grid_html(combined)
            return combined, gr.update(value=html), gr.update(visible=True), page_idx + 1, is_searching, search_results

    def load_more_popular(loaded_books, display_books, page_idx):
        start = page_idx * BOOKS_PER_LOAD
        end = start + BOOKS_PER_LOAD
        new_books = loaded_books.iloc[start:end]
        if new_books.empty:
            return display_books, gr.update(value=build_books_grid_html(display_books)), gr.update(visible=False), page_idx
        combined = pd.concat([display_books, new_books], ignore_index=True)
        html = build_books_grid_html(combined)
        return combined, gr.update(value=html), gr.update(visible=True), page_idx + 1

    def shuffle_random_books(loaded_books, display_books, is_searching, search_results):
        if is_searching:
            return loaded_books, display_books, gr.update(value=build_books_grid_html(display_books)), is_searching, search_results
        shuffled = loaded_books.sample(frac=1).reset_index(drop=True)
        initial_books = shuffled.iloc[:BOOKS_PER_LOAD]
        html = build_books_grid_html(initial_books)
        return shuffled, initial_books, html, is_searching, search_results

    # Search functions
    def perform_search(search_query, current_random_books, current_display_books, is_searching, search_results):
        if not search_query.strip():
            return clear_search(current_random_books, is_searching, search_results)
        
        search_results_df, books_html, load_more_visible, clear_visible = search_books(search_query, current_random_books, current_display_books)
        
        if search_results_df.empty:
            indicator_html = "<div class='search-results-indicator'>No results</div>"
        else:
            indicator_html = f"<div class='search-results-indicator'>{len(search_results_df)} results</div>"
        
        return (
            search_results_df, 
            books_html, 
            load_more_visible, 
            gr.update(visible=clear_visible), 
            gr.update(value=indicator_html, visible=True), 
            True, 
            search_results_df
        )

    def clear_search_handler(current_random_books, is_searching, search_results):
        search_input_clear = gr.update(value="")
        initial_books = current_random_books.iloc[:BOOKS_PER_LOAD]
        books_html = gr.update(value=build_books_grid_html(initial_books))
        load_more_visible = gr.update(visible=True)
        clear_visible = gr.update(visible=False)
        indicator_visible = gr.update(visible=False)
        
        return (
            search_input_clear, 
            initial_books, 
            books_html, 
            load_more_visible, 
            clear_visible, 
            indicator_visible, 
            False, 
            pd.DataFrame()
        )

    # Favorites functions
    def toggle_favorite(book_id, is_add, favorites_df, favorites_display):
        if is_add:
            return add_to_favorites(book_id, favorites_df, favorites_display)
        else:
            return remove_from_favorites(book_id, favorites_df, favorites_display)

    def update_favorites_count(favorites_df):
        count = len(favorites_df)
        return gr.update(value=f"<div class='favorites-count'>{count} book{'s' if count != 1 else ''}</div>")

    # Event handlers
    search_btn.click(
        perform_search,
        [search_input, random_books_state, random_display_state, is_searching_state, search_results_state],
        [random_display_state, random_books_container, load_more_btn, clear_btn, search_indicator, is_searching_state, search_results_state]
    )

    clear_btn.click(
        clear_search_handler,
        [random_books_state, is_searching_state, search_results_state],
        [search_input, random_display_state, random_books_container, load_more_btn, clear_btn, search_indicator, is_searching_state, search_results_state]
    )

    load_more_btn.click(
        load_more_random,
        [random_books_state, random_display_state, random_index_state, is_searching_state, search_results_state],
        [random_display_state, random_books_container, load_more_btn, random_index_state, is_searching_state, search_results_state]
    )

    shuffle_btn.click(
        shuffle_random_books,
        [random_books_state, random_display_state, is_searching_state, search_results_state],
        [random_books_state, random_display_state, random_books_container, is_searching_state, search_results_state]
    )

    popular_load_more_btn.click(
        load_more_popular,
        [popular_books_state, popular_display_state, popular_index_state],
        [popular_display_state, popular_books_container, popular_load_more_btn, popular_index_state]
    )

    favorites_load_more_btn.click(
        load_more_favorites,
        [favorites_state, favorites_display_state, favorites_index_state],
        [favorites_display_state, favorites_container, favorites_load_more_btn, favorites_index_state]
    )

    # Initialize all sections
    def initial_load_random(loaded_books):
        initial_books = loaded_books.iloc[:BOOKS_PER_LOAD]
        html = build_books_grid_html(initial_books)
        return initial_books, html, 1, False, pd.DataFrame()

    def initial_load_popular(loaded_books):
        initial_books = loaded_books.iloc[:BOOKS_PER_LOAD]
        html = build_books_grid_html(initial_books)
        return initial_books, html, 1

    def initial_load_favorites():
        return pd.DataFrame(), pd.DataFrame(), 0

    # Set initial values
    (random_display_state.value, random_books_container.value, 
     random_index_state.value, is_searching_state.value, 
     search_results_state.value) = initial_load_random(random_books_state.value)
    
    popular_display_state.value, popular_books_container.value, popular_index_state.value = initial_load_popular(popular_books_state.value)
    
    favorites_state.value, favorites_display_state.value, favorites_index_state.value = initial_load_favorites()

    # ---------- ENHANCED POPUP WITH FAVORITES ----------
    gr.HTML("""
    <div class="popup-overlay" id="popup-overlay"></div>
    <div class="popup-container" id="popup-container">
        <span class="popup-close" id="popup-close">&times;</span>
        <div class="popup-content" id="popup-content"></div>
    </div>

    <script>
    const overlay = document.getElementById('popup-overlay');
    const container = document.getElementById('popup-container');
    const closeBtn = document.getElementById('popup-close');
    const content = document.getElementById('popup-content');

    let originalScrollPosition = 0;
    let currentBookId = '';
    let isInFavorites = false;

    function escapeHtml(str) {
        return str ? String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;') : "";
    }

    function formatText(text) {
        if (!text) return 'No description available.';
        return text.replace(/\\n/g, '<br>');
    }

    function updateFavoritesButton() {
        const favoriteBtn = document.getElementById('favorite-action-btn');
        if (favoriteBtn) {
            if (isInFavorites) {
                favoriteBtn.innerHTML = '❤️ Remove from Favorites';
                favoriteBtn.className = 'remove-favorite-btn';
            } else {
                favoriteBtn.innerHTML = '🤍 Add to Favorites';
                favoriteBtn.className = 'favorite-btn';
            }
        }
    }

    document.addEventListener('click', function(e) {
        const card = e.target.closest('.book-card');
        if (!card) return;
        
        originalScrollPosition = window.scrollY || document.documentElement.scrollTop;
        currentBookId = card.dataset.id;
        
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
        
        // Check if book is in favorites (this would need backend integration)
        isInFavorites = false; // This should be set based on actual favorites data
        
        content.innerHTML = `
            <div style="display: flex; gap: 20px; align-items: flex-start; margin-bottom: 20px;">
                <img src="${img}" style="width: 180px; height: auto; border-radius: 8px; object-fit: cover; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
                <div style="flex: 1; color: #222;">
                    <h2 style="margin: 0 0 12px 0; color: #1a202c; border-bottom: 2px solid #667eea; padding-bottom: 8px;">${escapeHtml(title)}</h2>
                    <p style="margin: 0 0 8px 0; font-size: 15px;"><strong>Author(s):</strong> <span style="color: #667eea;">${escapeHtml(authors)}</span></p>
                    <p style="margin: 0 0 8px 0; font-size: 15px;"><strong>Genres:</strong> <span style="color: #764ba2;">${escapeHtml(genres)}</span></p>
                    <p style="margin: 0 0 8px 0; font-size: 15px;"><strong>Rating:</strong> ${stars} <strong style="color: #667eea;">${parseFloat(rating).toFixed(1)}</strong></p>
                </div>
            </div>
            <div class="detail-stats">
                <div class="detail-stat">
                    <div class="detail-stat-value">${escapeHtml(year)}</div>
                    <div class="detail-stat-label">PUBLICATION YEAR</div>
                </div>
                <div class="detail-stat">
                    <div class="detail-stat-value">${escapeHtml(pages)}</div>
                    <div class="detail-stat-label">PAGES</div>
                </div>
                <div class="detail-stat">
                    <div class="detail-stat-value">${Math.ceil(parseInt(pages) / 250) || 'N/A'}</div>
                    <div class="detail-stat-label">READING TIME (HOURS)</div>
                </div>
            </div>
            <div style="margin-top: 15px;">
                <h3 style="margin: 0 0 10px 0; color: #1a202c; font-size: 16px;">Description</h3>
                <div class="description-scroll">
                    ${formatText(escapeHtml(desc))}
                </div>
            </div>
            <div class="favorite-action-section">
                <button id="favorite-action-btn" class="${isInFavorites ? 'remove-favorite-btn' : 'favorite-btn'}" onclick="toggleFavorite()">
                    ${isInFavorites ? '❤️ Remove from Favorites' : '🤍 Add to Favorites'}
                </button>
            </div>
        `;
        
        overlay.style.display = 'block';
        container.style.display = 'block';
        document.body.style.overflow = 'hidden';
    });

    function toggleFavorite() {
        // This would trigger a Gradio event to add/remove from favorites
        isInFavorites = !isInFavorites;
        updateFavoritesButton();
        
        // Show feedback
        const feedback = document.createElement('div');
        feedback.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #48bb78; color: white; padding: 12px 20px; border-radius: 8px; z-index: 1002; box-shadow: 0 4px 12px rgba(0,0,0,0.3);';
        feedback.textContent = isInFavorites ? 'Added to favorites!' : 'Removed from favorites!';
        document.body.appendChild(feedback);
        
        setTimeout(() => {
            document.body.removeChild(feedback);
        }, 2000);
    }

    function closePopup() {
        overlay.style.display = 'none';
        container.style.display = 'none';
        document.body.style.overflow = 'auto';
        window.scrollTo(0, originalScrollPosition);
    }

    closeBtn.addEventListener('click', closePopup);
    overlay.addEventListener('click', closePopup);

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closePopup();
        }
    });

    container.addEventListener('click', function(e) {
        e.stopPropagation();
    });
    </script>
    """)

demo.launch()