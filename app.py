import ast
import pandas as pd
import gradio as gr
import random

# Load and prepare data
df = pd.read_csv("data_mini_books.csv")
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# Fill missing data
df["rating"] = df.get("rating", [round(random.uniform(3.5, 4.8), 1) for _ in range(len(df))])
df["year"] = df.get("year", [random.randint(1990, 2023) for _ in range(len(df))])
df["pages"] = df.get("pages", [random.randint(150, 600) for _ in range(len(df))])
df["description"] = df.get("description", ["No description available." for _ in range(len(df))])

# Global state
favorites = []
current_book_details = None

def create_book_card(book, index):
    """Create a book card with heart toggle button"""
    is_favorite = any(fav['id'] == book["id"] for fav in favorites)
    heart_icon = "❤️" if is_favorite else "🤍"
    heart_tooltip = "Remove from favorites" if is_favorite else "Add to favorites"
    
    # Generate star rating
    rating = book.get("rating", 0)
    full_stars = int(rating)
    half_star = rating % 1 >= 0.5
    stars = "⭐" * full_stars + ("⭐" if half_star else "") + "☆" * (5 - full_stars - (1 if half_star else 0))
    
    card_html = f"""
    <div class="book-card" data-id="{book['id']}">
        <div class="card-image">
            <img src="{book['image_url']}" alt="{book['title']}" 
                 onerror="this.src='https://via.placeholder.com/120x180/444/fff?text=No+Image'">
            <div class="card-badge">{book.get('year', 'N/A')}</div>
            <button class="heart-btn" title="{heart_tooltip}" onclick="toggleFavorite('{book['id']}')">
                {heart_icon}
            </button>
        </div>
        <div class="card-content">
            <h4 class="book-title" title="{book['title']}">{book['title']}</h4>
            <p class="book-authors">{', '.join(book['authors'][:2])}</p>
            <div class="book-rating">
                {stars} <span class="rating-text">({rating:.1f})</span>
            </div>
            <p class="book-genres">{', '.join(book['genres'][:2])}</p>
        </div>
    </div>
    """
    return card_html

def toggle_favorite(book_id):
    """Toggle favorite status for a book"""
    global favorites
    
    book = df[df['id'] == book_id].iloc[0].to_dict() if not df[df['id'] == book_id].empty else None
    if not book:
        return gr.update(), gr.update(), "Book not found!"
    
    # Toggle favorite
    if any(fav['id'] == book_id for fav in favorites):
        favorites = [fav for fav in favorites if fav['id'] != book_id]
        message = f"💔 Removed '{book['title']}' from favorites"
    else:
        favorites.append(book)
        message = f"❤️ Added '{book['title']}' to favorites"
    
    # Update displays
    books_html = create_books_grid()
    favorites_html = create_favorites_section()
    
    return books_html, favorites_html, message

def show_book_details(book_id):
    """Show book details in the side panel"""
    global current_book_details
    
    book = df[df['id'] == book_id].iloc[0].to_dict() if not df[df['id'] == book_id].empty else None
    if not book:
        return gr.update(visible=False), "", "primary", "❤️ Add to Favorites"
    
    current_book_details = book
    
    # Generate details HTML
    rating = book.get("rating", 0)
    full_stars = int(rating)
    half_star = rating % 1 >= 0.5
    stars = "⭐" * full_stars + ("⭐" if half_star else "") + "☆" * (5 - full_stars - (1 if half_star else 0))
    
    is_favorite = any(fav['id'] == book_id for fav in favorites)
    fav_text = "💔 Remove from Favorites" if is_favorite else "❤️ Add to Favorites"
    fav_variant = "secondary" if is_favorite else "primary"
    
    details_html = f"""
    <div class="details-content">
        <div class="details-header">
            <img src="{book['image_url']}" alt="{book['title']}" 
                 onerror="this.src='https://via.placeholder.com/200x300/444/fff?text=No+Image'">
            <div class="header-info">
                <h2>{book['title']}</h2>
                <p class="authors">{', '.join(book['authors'])}</p>
                <div class="rating-large">
                    {stars} <span>({rating:.1f})</span>
                </div>
            </div>
        </div>
        
        <div class="details-grid">
            <div class="detail-item">
                <span class="label">Year:</span>
                <span class="value">{book.get('year', 'N/A')}</span>
            </div>
            <div class="detail-item">
                <span class="label">Pages:</span>
                <span class="value">{book.get('pages', 'N/A')}</span>
            </div>
            <div class="detail-item">
                <span class="label">Genres:</span>
                <span class="value">{', '.join(book['genres'])}</span>
            </div>
        </div>
        
        <div class="description-section">
            <h3>Description</h3>
            <p>{book.get('description', 'No description available.')}</p>
        </div>
    </div>
    """
    
    return gr.update(visible=True), details_html, fav_variant, fav_text

def create_books_grid():
    """Create the main books grid"""
    books_html = '<div class="books-grid">'
    for i, (_, book) in enumerate(df.iterrows()):
        books_html += create_book_card(book, i)
    books_html += '</div>'
    return books_html

def create_favorites_section():
    """Create the favorites section"""
    if not favorites:
        return """
        <div class="empty-favorites">
            <div class="empty-icon">⭐</div>
            <h3>No favorites yet</h3>
            <p>Click the heart icon on any book to add it to your favorites!</p>
        </div>
        """
    
    favorites_html = '<div class="favorites-grid">'
    for book in favorites:
        is_favorite = True  # All books in favorites are... favorites!
        heart_icon = "❤️"
        
        fav_card = f"""
        <div class="favorite-card" data-id="{book['id']}">
            <div class="fav-image">
                <img src="{book['image_url']}" alt="{book['title']}" 
                     onerror="this.src='https://via.placeholder.com/80x120/444/fff?text=No+Image'">
                <div class="fav-heart">❤️</div>
            </div>
            <div class="fav-content">
                <h4 title="{book['title']}">{book['title']}</h4>
                <p>{', '.join(book['authors'][:1])}</p>
                <div class="fav-rating">⭐ {book.get('rating', 0):.1f}</div>
            </div>
        </div>
        """
        favorites_html += fav_card
    favorites_html += '</div>'
    return favorites_html

# Initialize
books_grid_html = create_books_grid()
favorites_html = create_favorites_section()

with gr.Blocks(css="""
    .app-container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 20px;
        background: #1a1a1a;
        color: white;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    .main-layout {
        display: grid;
        grid-template-columns: 1fr 400px;
        gap: 30px;
        align-items: start;
    }
    .books-section {
        background: #222;
        border-radius: 16px;
        padding: 25px;
        border: 1px solid #444;
    }
    .details-section {
        background: #222;
        border-radius: 16px;
        padding: 25px;
        border: 1px solid #444;
        position: sticky;
        top: 20px;
        max-height: 85vh;
        overflow-y: auto;
    }
    .favorites-section {
        background: #222;
        border-radius: 16px;
        padding: 25px;
        border: 1px solid #444;
        margin-top: 30px;
        grid-column: 1 / -1;
    }
    .books-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
        gap: 20px;
    }
    .book-card {
        background: #333;
        border-radius: 12px;
        padding: 15px;
        border: 1px solid #555;
        transition: all 0.3s ease;
        cursor: pointer;
        position: relative;
    }
    .book-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        border-color: #667eea;
    }
    .card-image {
        position: relative;
        margin-bottom: 12px;
    }
    .card-image img {
        width: 100%;
        height: 200px;
        object-fit: cover;
        border-radius: 8px;
        border: 1px solid #666;
    }
    .card-badge {
        position: absolute;
        top: 8px;
        right: 8px;
        background: #667eea;
        color: white;
        padding: 4px 8px;
        border-radius: 10px;
        font-size: 10px;
        font-weight: bold;
    }
    .heart-btn {
        position: absolute;
        top: 8px;
        left: 8px;
        background: rgba(0, 0, 0, 0.7);
        border: none;
        border-radius: 50%;
        width: 32px;
        height: 32px;
        color: white;
        font-size: 16px;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .heart-btn:hover {
        background: rgba(237, 137, 54, 0.9);
        transform: scale(1.1);
    }
    .card-content {
        text-align: center;
    }
    .book-title {
        font-size: 14px;
        font-weight: 700;
        color: #fff;
        margin: 0 0 6px 0;
        line-height: 1.3;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
    }
    .book-authors {
        font-size: 12px;
        color: #88c;
        margin: 0 0 8px 0;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 1;
        -webkit-box-orient: vertical;
    }
    .book-rating {
        font-size: 11px;
        color: #ffa500;
        margin: 0 0 6px 0;
    }
    .rating-text {
        font-size: 10px;
        color: #ccc;
    }
    .book-genres {
        font-size: 11px;
        color: #aaa;
        margin: 0;
    }
    /* Details Panel */
    .details-content {
        color: #eee;
    }
    .details-header {
        display: flex;
        gap: 20px;
        margin-bottom: 25px;
        padding-bottom: 20px;
        border-bottom: 1px solid #444;
    }
    .details-header img {
        width: 120px;
        height: 180px;
        object-fit: cover;
        border-radius: 8px;
        border: 1px solid #666;
        flex-shrink: 0;
    }
    .header-info {
        flex-grow: 1;
    }
    .header-info h2 {
        margin: 0 0 8px 0;
        color: #fff;
        font-size: 20px;
        line-height: 1.3;
    }
    .authors {
        color: #88c;
        margin: 0 0 12px 0;
        font-size: 14px;
    }
    .rating-large {
        font-size: 16px;
        color: #ffa500;
    }
    .details-grid {
        display: grid;
        gap: 12px;
        margin-bottom: 25px;
    }
    .detail-item {
        display: flex;
        justify-content: between;
        padding: 8px 0;
        border-bottom: 1px solid #333;
    }
    .label {
        font-weight: 600;
        color: #ccc;
        min-width: 80px;
    }
    .value {
        color: #fff;
        flex-grow: 1;
        text-align: right;
    }
    .description-section h3 {
        color: #fff;
        margin: 0 0 12px 0;
        font-size: 16px;
    }
    .description-section p {
        color: #ccc;
        line-height: 1.5;
        font-size: 14px;
        margin: 0;
        background: #2a2a2a;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #444;
    }
    /* Favorites Section */
    .favorites-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
        gap: 15px;
    }
    .favorite-card {
        background: #333;
        border-radius: 10px;
        padding: 12px;
        border: 1px solid #555;
        transition: all 0.3s ease;
    }
    .favorite-card:hover {
        transform: translateY(-2px);
        border-color: #ed8936;
    }
    .fav-image {
        position: relative;
        margin-bottom: 8px;
    }
    .fav-image img {
        width: 100%;
        height: 120px;
        object-fit: cover;
        border-radius: 6px;
        border: 1px solid #666;
    }
    .fav-heart {
        position: absolute;
        top: 5px;
        left: 5px;
        background: rgba(0, 0, 0, 0.7);
        border-radius: 50%;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
    }
    .fav-content h4 {
        font-size: 12px;
        margin: 0 0 4px 0;
        color: #fff;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        line-height: 1.3;
    }
    .fav-content p {
        font-size: 10px;
        color: #88c;
        margin: 0 0 4px 0;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 1;
        -webkit-box-orient: vertical;
    }
    .fav-rating {
        font-size: 10px;
        color: #ffa500;
    }
    .empty-favorites {
        text-align: center;
        padding: 40px 20px;
        color: #888;
    }
    .empty-icon {
        font-size: 48px;
        margin-bottom: 15px;
        opacity: 0.5;
    }
    .empty-favorites h3 {
        margin: 0 0 10px 0;
        color: #ccc;
    }
    .empty-favorites p {
        margin: 0;
        color: #999;
    }
    .feedback-toast {
        background: #48bb78;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        margin: 10px 0;
        text-align: center;
        font-weight: 600;
        grid-column: 1 / -1;
    }
    h1, h2 {
        color: #fff;
        margin-bottom: 20px;
    }
    .section-title {
        display: flex;
        align-items: center;
        gap: 10px;
        color: #fff;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 2px solid #667eea;
    }
""") as demo:

    with gr.Column(elem_classes="app-container"):
        gr.Markdown("# 📚 Book Discovery Hub")
        gr.Markdown("### Browse books, read details, and build your favorites collection")
        
        # Feedback message
        feedback = gr.HTML()
        
        with gr.Column(elem_classes="main-layout"):
            # Left: Books Grid
            with gr.Column(elem_classes="books-section"):
                gr.Markdown("## 📖 All Books")
                books_display = gr.HTML(books_grid_html)
            
            # Right: Details Panel
            with gr.Column(visible=False, elem_classes="details-section") as details_panel:
                details_content = gr.HTML()
                with gr.Row():
                    details_fav_btn = gr.Button("❤️ Add to Favorites", variant="primary")
                    details_close_btn = gr.Button("Close", variant="secondary")
        
        # Bottom: Favorites Section
        with gr.Column(elem_classes="favorites-section"):
            gr.Markdown("## ⭐ Your Favorite Books")
            favorites_display = gr.HTML(favorites_html)
    
    # Create click handlers for each book
    for i, book in df.iterrows():
        # Create hidden buttons for book clicks
        book_click_btn = gr.Button(f"click_{book['id']}", visible=False)
        book_click_btn.click(
            lambda bid=book['id']: show_book_details(bid),
            outputs=[details_panel, details_content, details_fav_btn, details_fav_btn]
        )
        
        # Create hidden buttons for heart toggles
        heart_btn = gr.Button(f"heart_{book['id']}", visible=False)
        heart_btn.click(
            lambda bid=book['id']: toggle_favorite(bid),
            outputs=[books_display, favorites_display, feedback]
        )
    
    # Details panel actions
    details_fav_btn.click(
        lambda: toggle_favorite(current_book_details['id']) if current_book_details else (gr.update(), gr.update(), "No book selected!"),
        outputs=[books_display, favorites_display, feedback]
    )
    
    details_close_btn.click(
        lambda: gr.update(visible=False),
        outputs=[details_panel]
    )

demo.launch(share = True)