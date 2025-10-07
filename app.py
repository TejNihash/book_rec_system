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

# Add additional book metrics
df["rating"] = df.get("rating", [random.uniform(3.5, 4.8) for _ in range(len(df))])
df["year"] = df.get("year", [random.randint(1990, 2023) for _ in range(len(df))])
df["pages"] = df.get("pages", [random.randint(150, 600) for _ in range(len(df))])

BOOKS_PER_LOAD = 12  # 2 rows × 6 columns

# ---------- Global favorites storage ----------
favorites_list = []

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
            <img src="{book['image_url']}" onerror="this.src='https://via.placeholder.com/150x200/667eea/white?text=No+Image'">
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

# ---------- Favorites Functions ----------
def add_to_favorites_simple(book_id):
    """Simple function to add book to favorites"""
    global favorites_list
    
    # Find the book in the dataframe
    book = df[df['id'] == book_id]
    if not book.empty:
        book_data = book.iloc[0].to_dict()
        
        # Add to favorites if not already there
        if book_id not in [fav['id'] for fav in favorites_list]:
            favorites_list.append(book_data)
            print(f"✅ Added book '{book_data['title']}' to favorites. Total favorites: {len(favorites_list)}")
        else:
            print(f"⚠️ Book '{book_data['title']}' is already in favorites")
            
        # Return updated favorites display
        favorites_df = pd.DataFrame(favorites_list)
        html = build_books_grid_html(favorites_df)
        load_more_visible = len(favorites_list) > BOOKS_PER_LOAD
        
        return favorites_df, html, gr.update(visible=load_more_visible), len(favorites_list)
    
    print(f"❌ Book with ID {book_id} not found")
    return pd.DataFrame(), favorites_container, favorites_load_more_btn, len(favorites_list)

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

def update_favorites_count(fav_count):
    """Update favorites count display"""
    return gr.HTML.update(value=f"""
    <div style="display: flex; align-items: center; margin-bottom: 12px;">
        <h2 style="margin: 0; color: #2d3748; border-left: 4px solid #ed8936; padding-left: 10px;">⭐ Favorites</h2>
        <div class="favorites-count">{fav_count} book{'s' if fav_count != 1 else ''}</div>
    </div>
    """)

# ---------- Gradio UI ----------
with gr.Blocks(css="""
.books-section {
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 12px;
    height: 450px;
    overflow-y: auto;
    margin-bottom: 20px;
    background: linear-gradient(135deg, #f7f7f7 0%, #ffffff 100%);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.books-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 12px;
}
.book-card {
    background: #ffffff;
    border-radius: 10px;
    padding: 8px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.12);
    cursor: pointer;
    text-align: left;
    transition: all 0.3s ease;
    border: 1px solid #eaeaea;
    height: 100%;
    display: flex;
    flex-direction: column;
}
.book-card:hover {
    transform: translateY(-3px) scale(1.02);
    box-shadow: 0 6px 16px rgba(0,0,0,0.2);
    border-color: #667eea;
}
.book-image-container {
    position: relative;
    margin-bottom: 8px;
}
.book-card img {
    width: 100%;
    height: 160px;
    object-fit: cover;
    border-radius: 6px;
    border: 1px solid #eee;
}
.book-badge {
    position: absolute;
    top: 6px;
    right: 6px;
    background: rgba(102, 126, 234, 0.9);
    color: white;
    padding: 2px 5px;
    border-radius: 8px;
    font-size: 9px;
    font-weight: bold;
}
.book-info {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    gap: 3px;
}
.book-title { 
    font-size: 12px;
    font-weight: 700; 
    color: #222; 
    line-height: 1.2;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    margin-bottom: 2px;
}
.book-authors { 
    font-size: 10px;
    color: #667eea; 
    font-weight: 600;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
    margin-bottom: 2px;
}
.book-rating {
    font-size: 9px;
    color: #ffa500;
    margin-bottom: 3px;
}
.book-meta {
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin-top: auto;
}
.book-pages {
    font-size: 9px;
    color: #666;
    font-weight: 500;
}
.book-genres {
    font-size: 8px;
    color: #888;
    font-style: italic;
}
.load-more-section {
    text-align: center;
    margin: 8px 0;
}
.load-more-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 8px 20px;
    border-radius: 18px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    font-size: 11px;
}
.load-more-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}
.favorite-btn {
    background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 18px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(237, 137, 54, 0.3);
    margin-top: 8px;
    font-size: 12px;
}
.favorite-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(237, 137, 54, 0.4);
}
.search-btn {
    background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 18px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(72, 187, 120, 0.3);
    font-size: 12px;
}
.search-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(72, 187, 120, 0.4);
}
.clear-btn {
    background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 18px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(245, 101, 101, 0.3);
    font-size: 12px;
}
.clear-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(245, 101, 101, 0.4);
}
.search-section {
    background: linear-gradient(135deg, #edf2f7 0%, #f7fafc 100%);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 20px;
    border: 1px solid #e2e8f0;
}
.search-header {
    font-size: 16px;
    font-weight: bold;
    color: #2d3748;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.search-results-indicator {
    background: #667eea;
    color: white;
    padding: 3px 10px;
    border-radius: 16px;
    font-size: 11px;
    font-weight: 600;
    margin-left: auto;
}
.section-title {
    font-size: 18px;
    font-weight: bold;
    color: #2d3748;
    margin-bottom: 12px;
    border-left: 4px solid #667eea;
    padding-left: 10px;
}
.favorites-count {
    background: #ed8936;
    color: white;
    padding: 3px 10px;
    border-radius: 16px;
    font-size: 11px;
    font-weight: 600;
    margin-left: 8px;
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
    padding: 20px;
    max-width: 650px;
    width: 90%;
    max-height: 80vh;
    overflow-y: auto;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    border: 2px solid #667eea;
    z-index: 1001;
}
.popup-close {
    position: absolute;
    top: 10px;
    right: 14px;
    cursor: pointer;
    font-size: 22px;
    font-weight: bold;
    color: #222;
    background: #f0f0f0;
    border-radius: 50%;
    width: 30px;
    height: 30px;
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
    line-height: 1.5;
    font-size: 14px;
    color: #222;
}
.detail-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin: 12px 0;
    padding: 10px;
    background: #f0f4ff;
    border-radius: 8px;
    border: 1px solid #d0d6ff;
}
.detail-stat {
    text-align: center;
}
.detail-stat-value {
    font-size: 14px;
    font-weight: bold;
    color: #667eea;
}
.detail-stat-label {
    font-size: 10px;
    color: #444;
    margin-top: 2px;
}
.description-scroll {
    max-height: 180px;
    overflow-y: auto;
    padding-right: 6px;
    margin-top: 8px;
}
.description-scroll::-webkit-scrollbar {
    width: 5px;
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
    margin-top: 16px;
    padding-top: 12px;
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

    # === POPULAR BOOKS SECTION ===
    gr.Markdown("## 📈 Popular Books")
    with gr.Column():
        popular_books_container = gr.HTML(elem_classes="books-section")
        
        with gr.Row():
            popular_load_more_btn = gr.Button("📚 Load More Popular Books", elem_classes="load-more-btn")

    # === FAVORITES SECTION (AT BOTTOM) ===
    with gr.Column():
        favorites_header = gr.HTML("""
        <div style="display: flex; align-items: center; margin-bottom: 12px;">
            <h2 style="margin: 0; color: #2d3748; border-left: 4px solid #ed8936; padding-left: 10px;">⭐ Favorites</h2>
            <div class="favorites-count">0 books</div>
        </div>
        """)
        
        favorites_container = gr.HTML(
            elem_classes="books-section", 
            value="<div style='text-align: center; padding: 40px; color: #666;'>No favorite books yet. Click the ❤️ button in book details to add some!</div>"
        )
        
        with gr.Row():
            favorites_load_more_btn = gr.Button("📚 Load More Favorites", elem_classes="load-more-btn", visible=False)

    # === HIDDEN FAVORITES COMPONENTS ===
    with gr.Row(visible=False):
        favorite_book_id = gr.Textbox(value="", label="Favorite Book ID")
        add_favorite_btn = gr.Button("Add Favorite")

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
            return clear_search_handler(current_random_books, is_searching, search_results)
        
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
    def handle_add_favorite(book_id):
        """Handle adding a favorite"""
        return add_to_favorites_simple(book_id)

    def load_more_favorites(favorites_df, favorites_display, page_idx):
        start = page_idx * BOOKS_PER_LOAD
        end = start + BOOKS_PER_LOAD
        new_books = favorites_df.iloc[start:end]
        
        if new_books.empty:
            return favorites_display, gr.update(value=build_books_grid_html(favorites_display)), gr.update(visible=False), page_idx
        
        combined = pd.concat([favorites_display, new_books], ignore_index=True)
        html = build_books_grid_html(combined)
        return combined, gr.update(value=html), gr.update(visible=True), page_idx + 1

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

    # Favorites trigger
    add_favorite_btn.click(
        handle_add_favorite,
        inputs=[favorite_book_id],
        outputs=[favorites_state, favorites_container, favorites_load_more_btn, favorites_header]
    ).then(
        update_favorites_count,
        inputs=[favorite_book_id],  # We'll use the count from the first function
        outputs=[favorites_header]
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

    # ---------- WORKING POPUP WITH FAVORITES ----------
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

    function escapeHtml(str) {
        return str ? String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;') : "";
    }

    function formatText(text) {
        if (!text) return 'No description available.';
        return text.replace(/\\n/g, '<br>');
    }

    // Simple function to add favorite
    function addToFavorites(bookId) {
        console.log('🎯 Adding to favorites:', bookId);
        
        // Find the hidden favorite components
        const favoriteIdInput = document.querySelector('input[aria-label="Favorite Book ID"]');
        const addFavoriteBtn = document.querySelector('button:contains("Add Favorite")');
        
        if (favoriteIdInput && addFavoriteBtn) {
            // Update the book ID
            favoriteIdInput.value = bookId;
            
            // Trigger input event (Gradio listens for this)
            favoriteIdInput.dispatchEvent(new Event('input', { bubbles: true }));
            
            // Small delay to ensure value is set, then click the button
            setTimeout(() => {
                addFavoriteBtn.click();
                console.log('✅ Favorite button clicked');
            }, 100);
            
        } else {
            console.log('❌ Could not find favorite components');
            console.log('Favorite ID Input:', favoriteIdInput);
            console.log('Add Favorite Button:', addFavoriteBtn);
        }
        
        // Show feedback
        showFeedback('❤️ Added to favorites!');
    }

    function showFeedback(message) {
        // Remove existing feedback if any
        const existingFeedback = document.querySelector('.favorite-feedback');
        if (existingFeedback) {
            existingFeedback.remove();
        }
        
        const feedback = document.createElement('div');
        feedback.className = 'favorite-feedback';
        feedback.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #48bb78;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            z-index: 1002;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            font-weight: 600;
        `;
        feedback.textContent = message;
        document.body.appendChild(feedback);
        
        setTimeout(() => {
            if (document.body.contains(feedback)) {
                document.body.removeChild(feedback);
            }
        }, 3000);
    }

    document.addEventListener('click', function(e) {
        const card = e.target.closest('.book-card');
        if (!card) return;
        
        originalScrollPosition = window.scrollY || document.documentElement.scrollTop;
        const bookId = card.dataset.id;
        
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
            <div style="display: flex; gap: 16px; align-items: flex-start; margin-bottom: 16px;">
                <img src="${img}" style="width: 160px; height: auto; border-radius: 8px; object-fit: cover; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
                <div style="flex: 1; color: #222;">
                    <h2 style="margin: 0 0 10px 0; color: #1a202c; border-bottom: 2px solid #667eea; padding-bottom: 6px; font-size: 18px;">${escapeHtml(title)}</h2>
                    <p style="margin: 0 0 6px 0; font-size: 14px;"><strong>Author(s):</strong> <span style="color: #667eea;">${escapeHtml(authors)}</span></p>
                    <p style="margin: 0 0 6px 0; font-size: 14px;"><strong>Genres:</strong> <span style="color: #764ba2;">${escapeHtml(genres)}</span></p>
                    <p style="margin: 0 0 6px 0; font-size: 14px;"><strong>Rating:</strong> ${stars} <strong style="color: #667eea;">${parseFloat(rating).toFixed(1)}</strong></p>
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
            <div style="margin-top: 12px;">
                <h3 style="margin: 0 0 8px 0; color: #1a202c; font-size: 16px;">Description</h3>
                <div class="description-scroll">
                    ${formatText(escapeHtml(desc))}
                </div>
            </div>
            <div class="favorite-action-section">
                <button class="favorite-btn" onclick="addToFavorites('${bookId}')">
                    🤍 Add to Favorites
                </button>
            </div>
        `;
        
        overlay.style.display = 'block';
        container.style.display = 'block';
        document.body.style.overflow = 'hidden';
    });

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