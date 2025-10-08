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

BOOKS_PER_LOAD = 12
favorites_list = []

# ---------- Simple Helper Functions ----------
def create_book_card(book, is_favorite=False):
    """Create a book card with heart toggle"""
    heart_icon = "❤️" if is_favorite else "🤍"
    return f"""
    <div class='book-card' data-id='{book["id"]}'>
        <div class='book-header'>
            <div class='book-title'>{book['title']}</div>
            <div class='heart-toggle' onclick='toggleFavorite("{book["id"]}")'>{heart_icon}</div>
        </div>
        <div class='book-image-container'>
            <img src='{book["image_url"]}' onerror="this.src='https://via.placeholder.com/150x220/444/fff?text=No+Image'">
        </div>
        <div class='book-authors'>by {', '.join(book['authors'])}</div>
        <div class='book-genres'>{', '.join(book['genres'][:2])}</div>
    </div>
    """

def build_books_grid(books_df):
    """Build the main books grid"""
    cards_html = []
    for _, book in books_df.iterrows():
        is_fav = any(fav['id'] == book['id'] for fav in favorites_list)
        cards_html.append(create_book_card(book, is_fav))
    return f"<div class='books-grid'>{''.join(cards_html)}</div>"

def build_favorites_grid():
    """Build the favorites grid"""
    if not favorites_list:
        return "<div class='no-favorites'>No favorites yet. Click the 🤍 icon to add books!</div>"
    
    cards_html = []
    for book in favorites_list:
        cards_html.append(create_book_card(book, True))
    return f"<div class='books-grid'>{''.join(cards_html)}</div>"

# ---------- Favorites Functions ----------
def toggle_favorite(book_id):
    """Toggle favorite status for a book"""
    global favorites_list
    
    # Check if book is already in favorites
    if any(fav['id'] == book_id for fav in favorites_list):
        # Remove from favorites
        favorites_list = [fav for fav in favorites_list if fav['id'] != book_id]
        message = "💔 Removed from favorites"
        action = "removed"
    else:
        # Add to favorites
        book_data = df[df['id'] == book_id].iloc[0].to_dict()
        favorites_list.append(book_data)
        message = "❤️ Added to favorites"
        action = "added"
    
    # Update both grids
    main_grid = build_books_grid(df.iloc[:BOOKS_PER_LOAD])
    fav_grid = build_favorites_grid()
    count = len(favorites_list)
    
    return main_grid, fav_grid, f"⭐ Favorites ({count})", message

def get_book_details(book_id):
    """Get detailed information for a book"""
    book = df[df['id'] == book_id].iloc[0]
    return f"""
    <div class='book-details'>
        <img src='{book['image_url']}' class='detail-image'>
        <h2>{book['title']}</h2>
        <p><strong>Authors:</strong> {', '.join(book['authors'])}</p>
        <p><strong>Genres:</strong> {', '.join(book['genres'])}</p>
        <p><strong>Description:</strong></p>
        <div class='description'>{book.get('description', 'No description available.')}</div>
        <div class='favorite-section'>
            <button class='detail-favorite-btn' onclick='toggleFavorite("{book_id}")'>
                {'💔 Remove from Favorites' if any(fav['id'] == book_id for fav in favorites_list) else '❤️ Add to Favorites'}
            </button>
        </div>
    </div>
    """

# ---------- Gradio UI ----------
with gr.Blocks(css="""
/* Main layout */
.container {
    display: flex;
    gap: 20px;
    margin-bottom: 30px;
}
.books-column {
    flex: 3;
}
.details-column {
    flex: 2;
    min-height: 600px;
}

/* Book cards */
.books-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 15px;
    margin-bottom: 30px;
}
.book-card {
    background: #333;
    border-radius: 12px;
    padding: 15px;
    border: 2px solid #444;
    cursor: pointer;
    transition: all 0.3s ease;
    color: #eee;
}
.book-card:hover {
    border-color: #667eea;
    transform: translateY(-2px);
}
.book-header {
    display: flex;
    justify-content: space-between;
    align-items: start;
    margin-bottom: 10px;
}
.book-title {
    font-weight: bold;
    font-size: 14px;
    line-height: 1.3;
    flex: 1;
    margin-right: 10px;
}
.heart-toggle {
    font-size: 18px;
    cursor: pointer;
    transition: transform 0.2s ease;
    flex-shrink: 0;
}
.heart-toggle:hover {
    transform: scale(1.2);
}
.book-image-container {
    margin-bottom: 8px;
}
.book-card img {
    width: 100%;
    height: 160px;
    object-fit: cover;
    border-radius: 8px;
}
.book-authors {
    font-size: 12px;
    color: #88c;
    margin-bottom: 5px;
}
.book-genres {
    font-size: 11px;
    color: #888;
    font-style: italic;
}

/* Details panel */
.details-panel {
    background: #222;
    border-radius: 12px;
    padding: 20px;
    border: 2px solid #444;
    color: #eee;
    height: 100%;
}
.book-details {
    text-align: center;
}
.detail-image {
    width: 200px;
    height: 280px;
    object-fit: cover;
    border-radius: 8px;
    margin-bottom: 15px;
}
.book-details h2 {
    margin: 0 0 15px 0;
    color: #fff;
    font-size: 20px;
}
.book-details p {
    margin: 8px 0;
    text-align: left;
}
.description {
    max-height: 150px;
    overflow-y: auto;
    padding: 10px;
    background: #333;
    border-radius: 6px;
    margin: 10px 0;
    font-size: 14px;
    line-height: 1.4;
}

/* Favorite button in details */
.favorite-section {
    margin-top: 20px;
    padding-top: 15px;
    border-top: 2px solid #ed8936;
}
.detail-favorite-btn {
    background: #ed8936;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 20px;
    font-weight: 600;
    cursor: pointer;
    font-size: 14px;
    width: 100%;
}
.detail-favorite-btn:hover {
    background: #dd6b20;
}

/* Favorites section */
.favorites-section {
    background: #222;
    border-radius: 12px;
    padding: 20px;
    border: 2px solid #444;
    margin-top: 20px;
}
.no-favorites {
    text-align: center;
    color: #888;
    padding: 40px;
    font-size: 16px;
}

/* Feedback */
.feedback {
    position: fixed;
    top: 20px;
    right: 20px;
    background: #48bb78;
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    z-index: 1000;
    font-weight: 600;
}
""") as demo:

    gr.Markdown("# 📚 Book Discovery")
    
    # Feedback element
    feedback = gr.HTML("")
    
    # Main content area
    with gr.Row():
        # Books grid column
        with gr.Column(scale=3):
            gr.Markdown("## 📚 All Books")
            books_grid = gr.HTML()
        
        # Details column
        with gr.Column(scale=2):
            gr.Markdown("## 📖 Book Details")
            details_panel = gr.HTML("""
                <div class='details-panel'>
                    <div style='text-align: center; color: #888; padding: 40px;'>
                        Click on any book to see details here
                    </div>
                </div>
            """)
    
    # Favorites section
    with gr.Row():
        with gr.Column():
            favorites_header = gr.Markdown("## ⭐ Favorites (0)")
            favorites_grid = gr.HTML("""
                <div class='favorites-section'>
                    <div class='no-favorites'>No favorites yet. Click the 🤍 icon to add books!</div>
                </div>
            """)

    # ---------- Functions ----------
    def handle_book_click(book_id):
        """Show book details when a book is clicked"""
        details_html = get_book_details(book_id)
        return details_html

    def handle_favorite_toggle(book_id):
        """Handle favorite toggle from JavaScript"""
        main_grid, fav_grid, header, message = toggle_favorite(book_id)
        
        # Update details panel if it's showing the same book
        current_details = get_book_details(book_id)
        
        # Create feedback message
        feedback_html = f"""
        <div class='feedback'>
            {message}
        </div>
        <script>
            setTimeout(() => {{
                document.querySelector('.feedback').style.display = 'none';
            }}, 2000);
        </script>
        """
        
        return main_grid, fav_grid, header, current_details, feedback_html

    # ---------- JavaScript Integration ----------
    gr.HTML("""
    <script>
    // Global function to toggle favorites
    function toggleFavorite(bookId) {
        // Send the toggle request to Gradio
        const url = new URL(window.location.href);
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                data: [bookId],
                fn_index: 1  // This should be the index of the favorite toggle function
            })
        }).then(response => response.json())
          .then(data => {
              // The page will update via Gradio's normal update mechanism
              console.log('Toggled favorite for book:', bookId);
          });
    }
    
    // Handle book card clicks for details
    document.addEventListener('click', function(e) {
        // Check if heart was clicked
        if (e.target.closest('.heart-toggle')) {
            const heart = e.target.closest('.heart-toggle');
            const bookCard = heart.closest('.book-card');
            const bookId = bookCard.dataset.id;
            toggleFavorite(bookId);
            return;
        }
        
        // Check if book card was clicked (but not the heart)
        const bookCard = e.target.closest('.book-card');
        if (bookCard && !e.target.closest('.heart-toggle')) {
            const bookId = bookCard.dataset.id;
            
            // Send book ID to Gradio to update details panel
            const url = new URL(window.location.href);
            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    data: [bookId],
                    fn_index: 0  // This should be the index of the details function
                })
            }).then(response => response.json())
              .then(data => {
                  console.log('Showing details for book:', bookId);
              });
        }
    });
    </script>
    """)

    # ---------- Initial Load ----------
    def initial_load():
        initial_books = df.iloc[:BOOKS_PER_LOAD]
        main_grid = build_books_grid(initial_books)
        fav_grid = build_favorites_grid()
        return main_grid, fav_grid, f"⭐ Favorites ({len(favorites_list)})"

    # Initialize
    books_grid.value, favorites_grid.value, favorites_header.value = initial_load()

demo.launch(share=True)