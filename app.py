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

def create_book_card(book, show_fav_button=True):
    """Create a book card with favorite button"""
    rating = book.get("rating", 0)
    stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
    if rating % 1 >= 0.5:
        stars = "⭐" * (int(rating)+1) + "☆" * (4 - int(rating))
    
    is_favorite = any(fav['id'] == book["id"] for fav in favorites_list)
    fav_text = "💔 Remove from Favorites" if is_favorite else "❤️ Add to Favorites"
    
    # Build HTML without problematic backslashes
    card_content = f"""
    <div class='book-card'>
        <div class='book-card-content'>
            <div class='book-image-section'>
                <img src="{book['image_url']}" onerror="this.src='https://via.placeholder.com/120x180/444/fff?text=No+Image'">
                <div class='book-year'>{book.get('year', 'N/A')}</div>
            </div>
            
            <div class='book-info-section'>
                <h3>{book['title']}</h3>
                <p class='book-authors'><strong>By:</strong> {', '.join(book['authors'])}</p>
                <p class='book-rating'><strong>Rating:</strong> {stars} ({rating:.1f})</p>
                <p class='book-meta'><strong>Pages:</strong> {book.get('pages', 'N/A')}</p>
                <p class='book-genres'><strong>Genres:</strong> {', '.join(book['genres'][:3])}</p>
                
                <div class='book-description'>
                    <p>{book.get('description', 'No description available.')}</p>
                </div>
            </div>
        </div>
    """
    
    if show_fav_button:
        card_content += f"""
        <div class='favorite-button-section'>
            <button class='favorite-btn {"remove" if is_favorite else ""}' onclick='toggleFavorite("{book['id']}")'>{fav_text}</button>
        </div>
        """
    
    card_content += "</div>"
    return card_content

def toggle_favorite(book_id):
    """Toggle favorite status"""
    global favorites_list
    
    # Find the book
    book_match = df[df['id'] == book_id]
    if book_match.empty:
        return "", "❌ Book not found!"
    
    book_data = book_match.iloc[0].to_dict()
    
    # Toggle favorite
    if any(fav['id'] == book_id for fav in favorites_list):
        favorites_list = [fav for fav in favorites_list if fav['id'] != book_id]
        message = f"💔 Removed '{book_data['title']}' from favorites!"
        print(f"❌ Removed '{book_data['title']}' from favorites")
    else:
        favorites_list.append(book_data)
        message = f"❤️ Added '{book_data['title']}' to favorites!"
        print(f"✅ Added '{book_data['title']}' to favorites")
    
    # Update all displays
    random_html = load_books_section(random_books, "")
    popular_html = load_books_section(popular_books, "")
    favorites_html = display_favorites()
    
    return random_html, popular_html, favorites_html, message

def display_favorites():
    """Display favorites section"""
    if not favorites_list:
        return """
        <div class='empty-state'>
            No favorite books yet. Click the favorite button on any book to add it!
        </div>
        """
    
    favorites_html = "<div class='favorites-grid'>"
    for book in favorites_list:
        favorites_html += create_book_card(book, True)
    favorites_html += "</div>"
    
    return favorites_html

def load_books_section(books_df, section_name):
    """Load a section of books"""
    if books_df.empty:
        return f"<div class='empty-state'>No books found</div>"
    
    section_html = "<div class='books-grid'>"
    for _, book in books_df.iterrows():
        section_html += create_book_card(book.to_dict(), True)
    section_html += "</div>"
    return section_html

def get_random_books():
    """Get random books"""
    return df.sample(n=min(8, len(df)))

def get_popular_books():
    """Get popular books (highest rated)"""
    return df.nlargest(8, 'rating')

# Initialize sections
random_books = get_random_books()
popular_books = get_popular_books()

with gr.Blocks(css="""
    .container { 
        max-width: 1200px; 
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
    }
    .book-card {
        background: #333;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        border: 1px solid #555;
        transition: all 0.3s ease;
    }
    .book-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.5);
        border-color: #667eea;
    }
    .book-card-content {
        display: flex;
        gap: 20px;
        align-items: flex-start;
    }
    .book-image-section {
        flex-shrink: 0;
        text-align: center;
    }
    .book-image-section img {
        width: 120px;
        height: 180px;
        object-fit: cover;
        border-radius: 8px;
        border: 1px solid #666;
    }
    .book-year {
        background: #667eea;
        color: white;
        padding: 4px 8px;
        border-radius: 10px;
        font-size: 11px;
        margin-top: 8px;
        display: inline-block;
    }
    .book-info-section {
        flex-grow: 1;
    }
    .book-info-section h3 {
        margin: 0 0 12px 0;
        color: #fff;
        font-size: 18px;
        border-bottom: 2px solid #667eea;
        padding-bottom: 8px;
    }
    .book-authors {
        margin: 0 0 8px 0;
        color: #88c;
        font-size: 14px;
    }
    .book-rating {
        margin: 0 0 8px 0;
        color: #ffa500;
        font-size: 14px;
    }
    .book-meta {
        margin: 0 0 8px 0;
        color: #ccc;
        font-size: 14px;
    }
    .book-genres {
        margin: 0 0 12px 0;
        color: #ccc;
        font-size: 14px;
    }
    .book-description {
        background: #222;
        padding: 12px;
        border-radius: 6px;
        border: 1px solid #444;
        max-height: 80px;
        overflow-y: auto;
    }
    .book-description p {
        margin: 0;
        color: #eee;
        font-size: 13px;
        line-height: 1.4;
    }
    .favorite-button-section {
        text-align: center;
        margin-top: 15px;
        padding-top: 15px;
        border-top: 1px solid #555;
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
        font-size: 14px;
    }
    .favorite-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(237,137,54,0.4);
    }
    .favorite-btn.remove {
        background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
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
    .books-grid, .favorites-grid {
        display: flex;
        flex-direction: column;
        gap: 15px;
    }
    h1, h2 {
        color: #fff;
        margin-bottom: 20px;
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
""") as demo:

    with gr.Column(elem_classes="container"):
        gr.Markdown("# 📚 Book Discovery Hub")
        gr.Markdown("### Explore and manage your favorite books")
        
        # Feedback message
        feedback = gr.HTML("")
        
        # Random Books Section
        with gr.Column(elem_classes="section"):
            gr.Markdown("## 🎲 Random Books")
            random_books_display = gr.HTML(load_books_section(random_books, ""))
            with gr.Row():
                shuffle_btn = gr.Button("🔄 Shuffle Random Books", variant="primary")
        
        # Popular Books Section  
        with gr.Column(elem_classes="section"):
            gr.Markdown("## 📈 Popular Books")
            popular_books_display = gr.HTML(load_books_section(popular_books, ""))
            with gr.Row():
                refresh_popular_btn = gr.Button("🔄 Refresh Popular Books", variant="primary")
        
        # Favorites Section
        with gr.Column(elem_classes="section"):
            gr.Markdown("## ⭐ Your Favorites")
            favorites_display = gr.HTML(display_favorites())
    
    # Event handlers for shuffle/refresh
    def shuffle_random():
        global random_books
        random_books = get_random_books()
        html = load_books_section(random_books, "")
        return html, "🔄 Shuffled random books!"
    
    def refresh_popular():
        global popular_books
        popular_books = get_popular_books()
        html = load_books_section(popular_books, "")
        return html, "🔄 Refreshed popular books!"
    
    # Create individual favorite toggle functions for each book
    favorite_functions = {}
    for _, book in df.iterrows():
        def create_favorite_handler(book_id):
            def handler():
                return toggle_favorite(book_id)
            return handler
        
        favorite_functions[book['id']] = create_favorite_handler(book['id'])
    
    # Set up event handlers
    shuffle_btn.click(
        lambda: (shuffle_random()[0], shuffle_random()[1]),
        outputs=[random_books_display, feedback]
    )
    
    refresh_popular_btn.click(
        lambda: (refresh_popular()[0], refresh_popular()[1]),
        outputs=[popular_books_display, feedback]
    )
    
    # Create hidden buttons for each book's favorite toggle
    for book_id in df['id'].values:
        btn = gr.Button(f"Toggle {book_id}", visible=False)
        btn.click(
            favorite_functions[book_id],
            outputs=[random_books_display, popular_books_display, favorites_display, feedback]
        )

demo.launch()