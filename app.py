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
def create_book_card_html(book):
    return f"""
    <div class='book-card' data-id='{book["id"]}' data-title="{book['title']}" 
         data-authors="{', '.join(book['authors'])}" data-img="{book['image_url']}" 
         data-desc="{book.get('description', 'No description')}">
        <div class='book-image-container'>
            <img src="{book['image_url']}" onerror="this.src='https://via.placeholder.com/150x220/444/fff?text=No+Image'">
        </div>
        <div class='book-info'>
            <div class='book-title'>{book['title']}</div>
            <div class='book-authors'>by {', '.join(book['authors'])}</div>
        </div>
    </div>
    """

def build_books_grid_html(books_df, is_favorites_section=False):
    if books_df.empty:
        if is_favorites_section:
            return "<div style='text-align: center; padding: 40px; color: #888;'>No favorite books yet. Click books below and use the favorite button!</div>"
        return "<div style='text-align: center; padding: 40px; color: #888;'>No books found</div>"
    
    cards_html = []
    for _, book in books_df.iterrows():
        cards_html.append(create_book_card_html(book))
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
        is_now_favorite = False
    else:
        # Add to favorites
        book_data = df[df['id'] == book_id].iloc[0].to_dict()
        favorites_list.append(book_data)
        message = "❤️ Added to favorites"
        is_now_favorite = True
    
    # Update favorites display
    favorites_df = pd.DataFrame(favorites_list)
    favorites_html = build_books_grid_html(favorites_df, is_favorites_section=True)
    
    # Update favorites header
    count_html = f"<h2>⭐ Favorites ({len(favorites_list)})</h2>"
    
    # Update toggle button text
    button_text = "💔 Remove from Favorites" if is_now_favorite else "❤️ Add to Favorites"
    
    return favorites_df, favorites_html, count_html, button_text, message

# ---------- Gradio UI ----------
with gr.Blocks(css="""
.books-section { border:1px solid #555; border-radius:12px; padding:16px; height:500px; overflow-y:auto; margin-bottom:20px; background:#222; }
.books-grid { display:grid; grid-template-columns:repeat(6,1fr); gap:16px; }
.book-card { background:#333; border-radius:12px; padding:10px; cursor:pointer; text-align:left; border:1px solid #555; height:100%; display:flex; flex-direction:column; color:#eee; }
.book-card:hover { border-color:#667eea; }
.book-image-container { margin-bottom:10px; }
.book-card img { width:100%; height:180px; object-fit:cover; border-radius:8px; border:1px solid #666; }
.book-info { flex-grow:1; }
.book-title { font-size:13px; font-weight:700; color:#fff; margin-bottom:2px; }
.book-authors { font-size:11px; color:#88c; }

.favorite-btn { background:#ed8936; color:white; border:none; padding:12px 24px; border-radius:20px; font-weight:600; cursor:pointer; margin:10px 0; font-size:14px; width:100%; }
.favorite-btn:hover { background:#dd6b20; }
.favorite-btn.remove { background:#f56565; }

/* Popup Styles */
.popup-overlay { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:99998; }
.popup-container { display:none; position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); background:#111; border-radius:16px; padding:24px; max-width:600px; width:90%; max-height:80vh; overflow-y:auto; border:2px solid #667eea; z-index:99999; color:#eee; }
.popup-close { position:absolute; top:12px; right:16px; cursor:pointer; font-size:24px; font-weight:bold; color:#fff; }
.popup-content { line-height:1.6; }
""") as demo:

    gr.Markdown("# 📚 Book Discovery")
    
    # Current book info
    current_book_info = gr.HTML("<div style='color: #888; padding: 10px; text-align: center;'>Click a book to see details</div>")
    
    # Favorite toggle button (initially hidden)
    favorite_toggle_btn = gr.Button("❤️ Add to Favorites", elem_classes="favorite-btn", visible=False)
    
    # Feedback
    feedback = gr.HTML("")
    
    # ---------- Books Sections ----------
    gr.Markdown("## 📚 All Books")
    books_container = gr.HTML(elem_classes="books-section")
    
    gr.Markdown("## ⭐ Favorites")
    favorites_header = gr.HTML("<h2>⭐ Favorites (0)</h2>")
    favorites_container = gr.HTML(elem_classes="books-section", value="<div style='text-align: center; padding: 40px; color: #888;'>No favorite books yet</div>")

    # ---------- States ----------
    favorites_state = gr.State(pd.DataFrame())
    current_book_state = gr.State(None)

    # ---------- Functions ----------
    def handle_book_click(book_data):
        """When a book is clicked, show it and enable the favorite button"""
        book_id = book_data["id"]
        book_title = book_data["title"]
        book_authors = ", ".join(book_data["authors"])
        
        # Check if book is favorited
        is_favorited = any(fav['id'] == book_id for fav in favorites_list)
        
        # Update book info display
        book_info_html = f"""
        <div style='color: #fff; padding: 10px; text-align: center; background: #333; border-radius: 8px;'>
            <strong>{book_title}</strong><br>
            <small style='color: #88c;'>by {book_authors}</small>
        </div>
        """
        
        # Update toggle button text and make it visible
        button_text = "💔 Remove from Favorites" if is_favorited else "❤️ Add to Favorites"
        
        return book_info_html, gr.update(value=button_text, visible=True), book_data

    def handle_favorite_toggle(current_book):
        """Handle the favorite toggle button click"""
        if current_book is None:
            return favorites_state.value, favorites_container.value, favorites_header.value, favorite_toggle_btn.value, "Please select a book first"
        
        book_id = current_book["id"]
        favorites_df, favorites_html, header, button_text, message = toggle_favorite(book_id)
        
        # Create feedback
        feedback_html = f"""
        <div style='background:#48bb78; color:white; padding:10px; border-radius:5px; text-align:center; margin:10px 0;'>
            {message}
        </div>
        """
        
        return favorites_df, favorites_html, header, gr.update(value=button_text), feedback_html

    # ---------- Event Handlers ----------
    # Favorite toggle button
    favorite_toggle_btn.click(
        handle_favorite_toggle,
        inputs=[current_book_state],
        outputs=[favorites_state, favorites_container, favorites_header, favorite_toggle_btn, feedback]
    )

    # ---------- Initial Load ----------
    def initial_load():
        initial_books = df.iloc[:BOOKS_PER_LOAD]
        html = build_books_grid_html(initial_books)
        return html

    # Initialize
    books_container.value = initial_load()

    # ---------- Simple Popup with Favorite Integration ----------
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

    // Function to update the current book info and favorite button
    function updateCurrentBook(bookData) {
        // This function would ideally update the Gradio components
        // For now, we'll just show the popup and let user use the visible favorite button
        console.log('Book selected:', bookData.title);
        
        // We'll assume the favorite button above will work for this book
        // The user needs to click the "Add to Favorites" button that's always visible
    }

    // Handle book card clicks
    document.addEventListener('click', function(e) {
        const card = e.target.closest('.book-card');
        if (!card) return;
        
        const bookData = {
            id: card.dataset.id,
            title: card.dataset.title,
            authors: card.dataset.authors,
            desc: card.dataset.desc,
            img: card.dataset.img
        };
        
        // Simple popup content
        content.innerHTML = `
            <div style="display: flex; gap: 20px; align-items: flex-start; margin-bottom: 20px;">
                <img src="${bookData.img}" style="width: 150px; height: auto; border-radius: 8px; object-fit: cover;">
                <div style="flex: 1;">
                    <h2 style="margin: 0 0 12px 0; color: #fff;">${bookData.title}</h2>
                    <p style="margin: 0 0 8px 0;"><strong>Author(s):</strong> ${bookData.authors}</p>
                </div>
            </div>
            
            <div style="margin-top: 16px;">
                <h3 style="margin: 0 0 10px 0; color: #fff;">Description</h3>
                <div style="max-height: 200px; overflow-y: auto; padding: 10px; background: #222; border-radius: 6px;">
                    ${bookData.desc}
                </div>
            </div>
            
            <div style="margin-top: 20px; padding-top: 15px; border-top: 2px solid #ed8936; text-align: center;">
                <p style="color: #888; font-size: 12px; margin-bottom: 10px;">
                    Use the "Add to Favorites" button above to toggle this book
                </p>
            </div>
        `;
        
        overlay.style.display = 'block';
        container.style.display = 'block';
        document.body.style.overflow = 'hidden';
        
        // Update current book for the favorite button
        updateCurrentBook(bookData);
    });

    function closePopup() {
        overlay.style.display = 'none';
        container.style.display = 'none';
        document.body.style.overflow = 'auto';
    }

    closeBtn.addEventListener('click', closePopup);
    overlay.addEventListener('click', closePopup);

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') closePopup();
    });

    container.addEventListener('click', function(e) {
        e.stopPropagation();
    });
    </script>
    """)

# Fix the launch command
demo.launch(share=True)