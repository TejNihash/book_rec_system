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
    fav_class = "favorite-btn remove" if is_favorite else "favorite-btn"
    
    card_html = f"""
    <div class='book-card' style='background:#333; border-radius:12px; padding:15px; margin:10px; border:1px solid #555;'>
        <div style='display: flex; gap: 15px;'>
            <!-- Book Image -->
            <div style='flex-shrink: 0;'>
                <img src="{book['image_url']}" 
                     style='width: 120px; height: 180px; object-fit: cover; border-radius:8px;'
                     onerror="this.src='https://via.placeholder.com/120x180/444/fff?text=No+Image'">
                <div style='background:#667eea; color:white; padding:2px 8px; border-radius:10px; font-size:10px; text-align:center; margin-top:5px;'>
                    {book.get('year', 'N/A')}
                </div>
            </div>
            
            <!-- Book Info -->
            <div style='flex-grow: 1;'>
                <h3 style='margin: 0 0 8px 0; color: #fff;'>{book['title']}</h3>
                <p style='margin: 0 0 6px 0; color: #88c; font-size: 14px;'><strong>By:</strong> {', '.join(book['authors'])}</p>
                <p style='margin: 0 0 6px 0; color: #ffa500; font-size: 14px;'><strong>Rating:</strong> {stars} ({rating:.1f})</p>
                <p style='margin: 0 0 6px 0; color: #ccc; font-size: 14px;'><strong>Pages:</strong> {book.get('pages', 'N/A')}</p>
                <p style='margin: 0 0 10px 0; color: #ccc; font-size: 14px;'><strong>Genres:</strong> {', '.join(book['genres'][:3])}</p>
                
                <!-- Description -->
                <div style='background:#222; padding:10px; border-radius:6px; border:1px solid #444; max-height: 80px; overflow-y: auto;'>
                    <p style='margin: 0; color: #eee; font-size: 13px; line-height: 1.4;'>
                        {book.get('description', 'No description available.')}
                    </p>
                </div>
            </div>
        </div>
        
        <!-- Favorite Button -->
        {f"<div style='text-align: center; margin-top: 15px;'><button class='{fav_class}' onclick='toggleFavorite(\"{book['id']}\")'>{fav_text}</button></div>" if show_fav_button else ""}
    </div>
    """
    return card_html

def toggle_favorite(book_id):
    """Toggle favorite status"""
    global favorites_list
    
    # Find the book
    book_match = df[df['id'] == book_id]
    if book_match.empty:
        return "", f"❌ Book not found!", gr.update()
    
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
    
    # Update favorites display
    favorites_html = display_favorites()
    return favorites_html, message, gr.update()

def display_favorites():
    """Display favorites section"""
    if not favorites_list:
        return """
        <div style='text-align: center; padding: 40px; color: #888; font-size: 16px;'>
            No favorite books yet. Click the favorite button on any book to add it!
        </div>
        """
    
    favorites_html = "<div style='display: flex; flex-direction: column; gap: 15px;'>"
    for book in favorites_list:
        favorites_html += create_book_card(book, show_fav_button=True)
    favorites_html += "</div>"
    
    return favorites_html

def load_books_section(books_df, section_name, show_fav_buttons=True):
    """Load a section of books"""
    if books_df.empty:
        return f"<div style='text-align: center; padding: 40px; color: #888;'>No {section_name} books found</div>"
    
    section_html = f"<h3 style='color: #fff; margin-bottom: 15px;'>{section_name}</h3>"
    section_html += "<div style='display: flex; flex-direction: column; gap: 15px;'>"
    
    for _, book in books_df.iterrows():
        section_html += create_book_card(book.to_dict(), show_fav_buttons)
    
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
    .container { max-width: 1200px; margin: 0 auto; padding: 20px; background: #1a1a1a; color: white; }
    .section { background: #222; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid #444; }
    .favorite-btn { 
        background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%); 
        color: white; border: none; padding: 10px 20px; 
        border-radius: 20px; font-weight: 600; cursor: pointer; 
        transition: all 0.3s ease; font-size: 14px; 
    }
    .favorite-btn:hover { 
        transform: translateY(-2px); 
        box-shadow: 0 6px 16px rgba(237,137,54,0.4); 
    }
    .favorite-btn.remove { 
        background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%); 
    }
    .book-card { transition: all 0.3s ease; }
    .book-card:hover { 
        transform: translateY(-2px); 
        box-shadow: 0 8px 20px rgba(0,0,0,0.7); 
        border-color: #667eea !important; 
    }
""") as demo:

    gr.Markdown("""
    # 📚 Book Discovery Hub
    ### Explore and manage your favorite books
    """)
    
    # Feedback message
    feedback = gr.HTML("")
    
    # Random Books Section
    with gr.Column(elem_classes="section"):
        gr.Markdown("## 🎲 Random Books")
        random_books_display = gr.HTML(load_books_section(random_books, "", True))
        with gr.Row():
            shuffle_btn = gr.Button("🔄 Shuffle Random Books", variant="primary")
    
    # Popular Books Section  
    with gr.Column(elem_classes="section"):
        gr.Markdown("## 📈 Popular Books")
        popular_books_display = gr.HTML(load_books_section(popular_books, "", True))
        with gr.Row():
            refresh_popular_btn = gr.Button("🔄 Refresh Popular Books", variant="primary")
    
    # Favorites Section
    with gr.Column(elem_classes="section"):
        gr.Markdown("## ⭐ Your Favorites")
        favorites_display = gr.HTML(display_favorites())
    
    # JavaScript for favorite buttons
    gr.HTML(f"""
    <script>
    function toggleFavorite(bookId) {{
        // This will be handled by Gradio events
        console.log('Toggling favorite for book:', bookId);
    }}
    
    // Store book data for reference
    window.bookData = {df[['id', 'title']].to_dict('records')};
    </script>
    """)
    
    # Event handlers for shuffle/refresh
    def shuffle_random():
        global random_books
        random_books = get_random_books()
        return load_books_section(random_books, "", True)
    
    def refresh_popular():
        global popular_books
        popular_books = get_popular_books()
        return load_books_section(popular_books, "", True)
    
    shuffle_btn.click(shuffle_random, outputs=random_books_display)
    refresh_popular_btn.click(refresh_popular, outputs=popular_books_display)
    
    # Create individual favorite buttons for each book
    for i, book in df.iterrows():
        # Create a hidden button for each book that can be triggered by JavaScript
        btn = gr.Button(f"Toggle Favorite {book['id']}", visible=False)
        btn.click(
            lambda bid=book['id']: toggle_favorite(bid),
            outputs=[favorites_display, feedback, btn]
        )

demo.launch()