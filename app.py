import ast
import pandas as pd
import gradio as gr
import random

# Load data
df = pd.read_csv("data_mini_books.csv")
if "id" not in df.columns:
    df["id"] = df.index.astype(str)
df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# Global favorites
favorites = []

# Create the interface
with gr.Blocks() as demo:
    gr.Markdown("# 📚 Simple Book App")
    
    # Current book display
    current_book = gr.HTML("<div style='text-align: center; color: #666; padding: 20px;'>Click a book below</div>")
    
    # Favorite button
    fav_btn = gr.Button("⭐ Add to Favorites", size="lg")
    
    # Feedback
    feedback = gr.HTML()
    
    # Books grid
    gr.Markdown("## All Books")
    books_html = gr.HTML()
    
    # Favorites section
    gr.Markdown("## ⭐ Favorites")
    favorites_html = gr.HTML("<div style='text-align: center; color: #666; padding: 40px;'>No favorites yet</div>")
    
    # Hidden state
    current_book_id = gr.State()
    
    # Functions
    def create_book_card(book):
        return f"""
        <div style='border: 1px solid #ccc; border-radius: 10px; padding: 15px; text-align: center; cursor: pointer; background: white;'>
            <img src="{book['image_url']}" style="width: 120px; height: 160px; object-fit: cover; border-radius: 5px;">
            <div style="margin-top: 10px;">
                <strong>{book['title'][:30]}{'...' if len(book['title']) > 30 else ''}</strong>
            </div>
            <div style="color: #666; font-size: 12px;">
                by {', '.join(book['authors'])[:25]}
            </div>
        </div>
        """
    
    def build_books_grid():
        books = df.head(12)
        cards = []
        for _, book in books.iterrows():
            cards.append(f"""
            <div onclick="selectBook('{book["id"]}')">
                {create_book_card(book)}
            </div>
            """)
        return f"<div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;'>{''.join(cards)}</div>"
    
    def build_favorites_grid():
        if not favorites:
            return "<div style='text-align: center; color: #666; padding: 40px;'>No favorites yet</div>"
        
        cards = []
        for book in favorites:
            cards.append(create_book_card(book))
        return f"<div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;'>{''.join(cards)}</div>"
    
    def select_book(book_id):
        book = df[df['id'] == book_id].iloc[0]
        book_display = f"""
        <div style='text-align: center; background: #f5f5f5; padding: 20px; border-radius: 10px;'>
            <img src="{book['image_url']}" style="width: 150px; height: 200px; object-fit: cover; border-radius: 5px;">
            <h3>{book['title']}</h3>
            <p>by {', '.join(book['authors'])}</p>
        </div>
        """
        
        # Check if already favorited
        is_fav = any(fav['id'] == book_id for fav in favorites)
        btn_text = "💔 Remove from Favorites" if is_fav else "⭐ Add to Favorites"
        
        return book_display, book_id, btn_text
    
    def toggle_favorite(book_id):
        if not book_id:
            return current_book.value, fav_btn.value, favorites_html.value, "Please select a book first!"
        
        book = df[df['id'] == book_id].iloc[0]
        
        # Toggle favorite
        if any(fav['id'] == book_id for fav in favorites):
            favorites[:] = [fav for fav in favorites if fav['id'] != book_id]
            message = f"Removed {book['title']} from favorites"
            btn_text = "⭐ Add to Favorites"
        else:
            favorites.append(book)
            message = f"Added {book['title']} to favorites!"
            btn_text = "💔 Remove from Favorites"
        
        # Update displays
        fav_display = build_favorites_grid()
        feedback_msg = f"<div style='background: #4CAF50; color: white; padding: 10px; border-radius: 5px; text-align: center;'>{message}</div>"
        
        return current_book.value, btn_text, fav_display, feedback_msg
    
    # Event handlers
    fav_btn.click(
        toggle_favorite,
        inputs=[current_book_id],
        outputs=[current_book, fav_btn, favorites_html, feedback]
    )
    
    # JavaScript for book selection
    gr.HTML(f"""
    <script>
    function selectBook(bookId) {{
        // This would normally call a Gradio function, but for simplicity we'll use a workaround
        console.log('Selected book:', bookId);
        
        // For now, we'll just show an alert. In a real app, this would update the Gradio components
        alert('Book selected! Now click the "Add to Favorites" button above.');
        
        // Store the selected book ID in a global variable
        window.selectedBookId = bookId;
        
        // Try to find and update the current book display
        const bookDisplay = document.querySelector('[data-testid="current-book"]');
        if (bookDisplay) {{
            // This is a simplified version - in reality you'd need to call the Python function
            bookDisplay.innerHTML = '<div style="text-align: center; color: green; padding: 20px;">Book selected! ID: ' + bookId + '</div>';
        }}
    }}
    </script>
    
    <!-- Initialize the books grid -->
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        // This would normally be set by the Python function
        const booksGrid = `{build_books_grid()}`;
        const gridElement = document.querySelector('[data-testid="books-html"]');
        if (gridElement) {{
            gridElement.innerHTML = booksGrid;
        }}
    }});
    </script>
    """)
    
    # Initialize
    books_html.value = build_books_grid()

demo.launch(share=True)