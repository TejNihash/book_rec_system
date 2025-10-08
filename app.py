import ast
import pandas as pd
import gradio as gr
import random

# Load dataset
df = pd.read_csv("data_mini_books.csv")
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# Fill missing data
df["rating"] = df.get("rating", [random.uniform(3.5, 4.8) for _ in range(len(df))])
df["year"] = df.get("year", [random.randint(1990, 2023) for _ in range(len(df))])
df["pages"] = df.get("pages", [random.randint(150, 600) for _ in range(len(df))])

BOOKS_PER_LOAD = 12
favorites_list = []

def create_book_card(book, index):
    """Create a compact book card with details button"""
    rating = book.get("rating", 0)
    stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
    if rating % 1 >= 0.5:
        stars = "⭐" * (int(rating)+1) + "☆" * (4 - int(rating))
    
    is_favorite = any(fav['id'] == book["id"] for fav in favorites_list)
    fav_icon = "❤️" if is_favorite else "🤍"
    
    card_html = f"""
    <div class='book-card' style='position: relative;'>
        <div class='book-card-compact'>
            <img src="{book['image_url']}" onerror="this.src='https://via.placeholder.com/100x150/444/fff?text=No+Image'">
            <div class='book-badge'>{book.get('year', 'N/A')}</div>
            <div class='favorite-indicator'>{fav_icon}</div>
            <div class='book-info-compact'>
                <div class='book-title' title="{book['title']}">{book['title']}</div>
                <div class='book-authors'>{', '.join(book['authors'][:2])}</div>
                <div class='book-rating'>{stars}</div>
            </div>
        </div>
    </div>
    """
    return card_html

def show_book_details(book_id, visible=True):
    """Show book details in popup"""
    book_match = df[df['id'] == book_id]
    if book_match.empty:
        return gr.update(visible=False), "", "", ""
    
    book = book_match.iloc[0]
    rating = book.get("rating", 0)
    stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
    if rating % 1 >= 0.5:
        stars = "⭐" * (int(rating)+1) + "☆" * (4 - int(rating))
    
    is_favorite = any(fav['id'] == book_id for fav in favorites_list)
    
    # Create details content
    details_html = f"""
    <div class='popup-content'>
        <div class='popup-header'>
            <h3>{book['title']}</h3>
        </div>
        <div class='popup-body'>
            <div class='popup-image'>
                <img src="{book['image_url']}" onerror="this.src='https://via.placeholder.com/150x220/444/fff?text=No+Image'">
            </div>
            <div class='popup-details'>
                <p><strong>Authors:</strong> {', '.join(book['authors'])}</p>
                <p><strong>Rating:</strong> {stars} ({rating:.1f})</p>
                <p><strong>Year:</strong> {book.get('year', 'N/A')}</p>
                <p><strong>Pages:</strong> {book.get('pages', 'N/A')}</p>
                <p><strong>Genres:</strong> {', '.join(book['genres'])}</p>
                <div class='description'>
                    <strong>Description:</strong>
                    <p>{book.get('description', 'No description available.')}</p>
                </div>
            </div>
        </div>
    </div>
    """
    
    fav_button_text = "💔 Remove from Favorites" if is_favorite else "❤️ Add to Favorites"
    fav_button_variant = "secondary" if is_favorite else "primary"
    
    return gr.update(visible=visible), details_html, fav_button_text, fav_button_variant

def toggle_favorite_from_popup(book_id):
    """Toggle favorite from popup button"""
    global favorites_list
    
    book_match = df[df['id'] == book_id]
    if book_match.empty:
        return "❌ Book not found!", "", "primary"
    
    book_data = book_match.iloc[0].to_dict()
    
    # Toggle favorite
    if any(fav['id'] == book_id for fav in favorites_list):
        favorites_list = [fav for fav in favorites_list if fav['id'] != book_id]
        message = f"💔 Removed '{book_data['title']}' from favorites!"
        new_text = "❤️ Add to Favorites"
        new_variant = "primary"
    else:
        favorites_list.append(book_data)
        message = f"❤️ Added '{book_data['title']}' to favorites!"
        new_text = "💔 Remove from Favorites"
        new_variant = "secondary"
    
    # Update all displays
    random_html = load_books_section(random_books, "random")
    popular_html = load_books_section(popular_books, "popular")
    favorites_html = display_favorites()
    
    return message, new_text, new_variant, random_html, popular_html, favorites_html

def display_favorites():
    """Display favorites section"""
    if not favorites_list:
        return """
        <div class='empty-state'>
            No favorite books yet. Click the favorite button in book details to add some!
        </div>
        """
    
    favorites_html = "<div class='favorites-grid'>"
    for i, book in enumerate(favorites_list):
        favorites_html += create_book_card(book, i)
    favorites_html += "</div>"
    
    return favorites_html

def load_books_section(books_df, section_type):
    """Load a section of books"""
    if books_df.empty:
        return "<div class='empty-state'>No books found</div>"
    
    section_html = f"<div class='books-grid {section_type}'>"
    for i, (_, book) in enumerate(books_df.iterrows()):
        section_html += create_book_card(book.to_dict(), i)
    section_html += "</div>"
    return section_html

def get_random_books():
    """Get random books"""
    return df.sample(n=min(12, len(df)))

def get_popular_books():
    """Get popular books (highest rated)"""
    return df.nlargest(12, 'rating')

# Initialize sections
random_books = get_random_books()
popular_books = get_popular_books()

with gr.Blocks(css="""
    .container { 
        max-width: 1400px; 
        margin: 0 auto; 
        padding: 20px; 
        background: #1a1a1a; 
        color: white; 
        font-family: Arial, sans-serif;
    }
    .section { 
        background: #222; 
        border-radius: 12px; 
        padding: 25px; 
        margin-bottom: 25px; 
        border: 1px solid #444; 
        position: relative;
    }
    .books-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
        gap: 20px;
        margin-top: 15px;
    }
    .book-card {
        position: relative;
    }
    .book-card-compact {
        background: #333;
        border-radius: 12px;
        padding: 15px;
        border: 1px solid #555;
        transition: all 0.3s ease;
        cursor: pointer;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    .book-card-compact:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        border-color: #667eea;
    }
    .book-card-compact img {
        width: 100%;
        height: 200px;
        object-fit: cover;
        border-radius: 8px;
        margin-bottom: 10px;
        border: 1px solid #666;
    }
    .book-badge {
        position: absolute;
        top: 20px;
        right: 20px;
        background: #667eea;
        color: white;
        padding: 4px 8px;
        border-radius: 10px;
        font-size: 10px;
        font-weight: bold;
    }
    .favorite-indicator {
        position: absolute;
        top: 20px;
        left: 20px;
        font-size: 16px;
    }
    .book-info-compact {
        flex-grow: 1;
    }
    .book-title {
        font-size: 14px;
        font-weight: bold;
        color: #fff;
        margin-bottom: 5px;
        line-height: 1.3;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
    }
    .book-authors {
        font-size: 12px;
        color: #88c;
        margin-bottom: 5px;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 1;
        -webkit-box-orient: vertical;
    }
    .book-rating {
        font-size: 11px;
        color: #ffa500;
    }
    .popup-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        backdrop-filter: blur(5px);
        z-index: 1000;
        display: none;
    }
    .popup-container {
        position: absolute;
        background: #222;
        border-radius: 12px;
        border: 2px solid #667eea;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8);
        z-index: 1001;
        max-width: 500px;
        width: 90vw;
        max-height: 80vh;
        overflow-y: auto;
    }
    .popup-content {
        padding: 0;
    }
    .popup-header {
        background: #667eea;
        padding: 20px;
        border-radius: 10px 10px 0 0;
    }
    .popup-header h3 {
        margin: 0;
        color: white;
        font-size: 18px;
    }
    .popup-body {
        padding: 20px;
        display: flex;
        gap: 20px;
    }
    .popup-image {
        flex-shrink: 0;
    }
    .popup-image img {
        width: 150px;
        height: 220px;
        object-fit: cover;
        border-radius: 8px;
        border: 1px solid #666;
    }
    .popup-details {
        flex-grow: 1;
    }
    .popup-details p {
        margin: 0 0 10px 0;
        color: #eee;
        font-size: 14px;
        line-height: 1.4;
    }
    .popup-details strong {
        color: #fff;
    }
    .description {
        margin-top: 15px;
        padding: 15px;
        background: #2a2a2a;
        border-radius: 8px;
        border: 1px solid #444;
    }
    .description p {
        margin: 8px 0 0 0;
        color: #ccc;
        font-style: italic;
    }
    .popup-actions {
        padding: 20px;
        border-top: 1px solid #444;
        text-align: center;
    }
    .empty-state {
        text-align: center;
        padding: 40px;
        color: #888;
        font-size: 16px;
        background: #2a2a2a;
        border-radius: 8px;
        border: 1px solid #555;
    }
    .favorites-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
        gap: 20px;
    }
    .feedback-message {
        background: #48bb78;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        margin: 10px 0;
        text-align: center;
        font-weight: 600;
    }
    .close-popup-btn {
        position: absolute;
        top: 10px;
        right: 15px;
        background: #f56565;
        color: white;
        border: none;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        cursor: pointer;
        font-size: 16px;
        font-weight: bold;
        z-index: 1002;
    }
""") as demo:

    with gr.Column(elem_classes="container"):
        gr.Markdown("# 📚 Book Discovery Hub")
        gr.Markdown("### Explore and manage your favorite books")
        
        # Feedback message
        feedback = gr.HTML("")
        
        # Hidden popup components
        popup_visible = gr.Checkbox(False, visible=False)
        current_book_id = gr.Textbox("", visible=False)
        popup_position_x = gr.Number(0, visible=False)
        popup_position_y = gr.Number(0, visible=False)
        
        # Random Books Section
        with gr.Column(elem_classes="section"):
            gr.Markdown("## 🎲 Random Books")
            random_books_display = gr.HTML(load_books_section(random_books, "random"))
            shuffle_btn = gr.Button("🔄 Shuffle Random Books", variant="primary")
        
        # Popular Books Section  
        with gr.Column(elem_classes="section"):
            gr.Markdown("## 📈 Popular Books")
            popular_books_display = gr.HTML(load_books_section(popular_books, "popular"))
            refresh_popular_btn = gr.Button("🔄 Refresh Popular Books", variant="primary")
        
        # Favorites Section
        with gr.Column(elem_classes="section"):
            gr.Markdown("## ⭐ Your Favorites")
            favorites_display = gr.HTML(display_favorites())
        
        # Popup Components (initially hidden)
        with gr.Column(visible=False) as popup_column:
            popup_content = gr.HTML()
            with gr.Row():
                favorite_btn = gr.Button("❤️ Add to Favorites", variant="primary")
                close_btn = gr.Button("✕ Close", variant="secondary")
    
    # Create click handlers for each book
    book_click_handlers = []
    for _, book in df.iterrows():
        def create_click_handler(bid=book['id']):
            def handler():
                return (
                    gr.update(visible=True),  # Show popup
                    *show_book_details(bid, True)  # Content, button text, variant
                )
            return handler
        book_click_handlers.append(create_click_handler())
    
    # Set up event handlers
    shuffle_btn.click(
        lambda: (load_books_section(get_random_books(), "random"), "🔄 Shuffled random books!"),
        outputs=[random_books_display, feedback]
    )
    
    refresh_popular_btn.click(
        lambda: (load_books_section(get_popular_books(), "popular"), "🔄 Refreshed popular books!"),
        outputs=[popular_books_display, feedback]
    )
    
    # Book click handlers (using the first 24 books for demo)
    for i in range(min(24, len(df))):
        btn = gr.Button(f"Book {i}", visible=False)
        btn.click(
            book_click_handlers[i],
            outputs=[popup_column, popup_content, favorite_btn, favorite_btn]
        )
    
    # Popup actions
    favorite_btn.click(
        lambda bid: toggle_favorite_from_popup(bid),
        inputs=[current_book_id],
        outputs=[feedback, favorite_btn, favorite_btn, random_books_display, popular_books_display, favorites_display]
    )
    
    close_btn.click(
        lambda: gr.update(visible=False),
        outputs=[popup_column]
    )

demo.launch()