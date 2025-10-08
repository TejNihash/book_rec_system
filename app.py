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

df["rating"] = df.get("rating", [random.uniform(3.5, 4.8) for _ in range(len(df))])
df["year"] = df.get("year", [random.randint(1990, 2023) for _ in range(len(df))])
df["pages"] = df.get("pages", [random.randint(150, 600) for _ in range(len(df))])

BOOKS_PER_LOAD = 12

# ---------- Global Favorites Storage ----------
favorites_list = []

# ---------- Simple Helper Functions ----------
def create_book_card_html(book, is_favorite=False):
    rating = book.get("rating", 0)
    stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
    if rating % 1 >= 0.5:
        stars = "⭐" * (int(rating)+1) + "☆" * (4 - int(rating))
    
    favorite_indicator = "❤️ " if is_favorite else ""
    
    return f"""
    <div class='book-card' data-id='{book["id"]}' data-title="{book['title']}" 
         data-authors="{', '.join(book['authors'])}" data-genres="{', '.join(book['genres'])}" 
         data-img="{book['image_url']}" data-desc="{book.get('description', 'No description')}"
         data-rating="{rating}" data-year="{book.get('year', 'N/A')}" data-pages="{book.get('pages', 'N/A')}">
        <div class='book-image-container'>
            <img src="{book['image_url']}" onerror="this.src='https://via.placeholder.com/150x220/444/fff?text=No+Image'">
            <div class='book-badge'>{book.get('year', 'N/A')}</div>
        </div>
        <div class='book-info'>
            <div class='book-title' title="{book['title']}">{favorite_indicator}{book['title']}</div>
            <div class='book-authors'>by {', '.join(book['authors'])}</div>
            <div class='book-rating'>{stars} ({rating:.1f})</div>
            <div class='book-meta'>
                <span class='book-pages'>{book.get('pages', 'N/A')} pages</span>
                <span class='book-genres'>{', '.join(book['genres'][:2])}{'...' if len(book['genres'])>2 else ''}</span>
            </div>
        </div>
    </div>
    """

def build_books_grid_html(books_df, is_favorites_section=False):
    if books_df.empty:
        if is_favorites_section:
            return "<div style='text-align: center; padding: 40px; color: #888; font-size: 16px;'>No favorite books yet. Click the favorite button in book details to add some!</div>"
        return "<div style='text-align: center; padding: 40px; color: #888;'>No books found</div>"
    
    cards_html = []
    for _, book in books_df.iterrows():
        is_fav = is_favorites_section or any(fav['id'] == book['id'] for fav in favorites_list)
        cards_html.append(create_book_card_html(book, is_fav))
    return f"<div class='books-grid'>{''.join(cards_html)}</div>"

# ---------- SIMPLE Favorites Functions ----------
def add_to_favorites(book_id):
    """Simple function to add book to favorites"""
    global favorites_list
    
    # Find the book
    book_match = df[df['id'] == book_id]
    if not book_match.empty:
        book_data = book_match.iloc[0].to_dict()
        
        # Add if not already there
        if not any(fav['id'] == book_id for fav in favorites_list):
            favorites_list.append(book_data)
            print(f"✅ Added '{book_data['title']}' to favorites")
            return True, f"❤️ Added '{book_data['title']}' to favorites!"
        else:
            return False, "⚠️ Already in favorites!"
    
    return False, "❌ Book not found!"

def remove_from_favorites(book_id):
    """Simple function to remove book from favorites"""
    global favorites_list
    
    book_title = None
    for fav in favorites_list:
        if fav['id'] == book_id:
            book_title = fav['title']
            break
            
    favorites_list = [fav for fav in favorites_list if fav['id'] != book_id]
    
    if book_title:
        print(f"❌ Removed '{book_title}' from favorites")
        return True, f"💔 Removed '{book_title}' from favorites!"
    
    return False, "❌ Book not found in favorites!"

def toggle_favorite(book_id):
    """Simple toggle function"""
    if any(fav['id'] == book_id for fav in favorites_list):
        return remove_from_favorites(book_id)
    else:
        return add_to_favorites(book_id)

def update_favorites_display():
    """Update the favorites section"""
    favorites_df = pd.DataFrame(favorites_list)
    html = build_books_grid_html(favorites_df, is_favorites_section=True)
    load_more_visible = len(favorites_list) > BOOKS_PER_LOAD
    
    count_html = f"""
    <div style="display: flex; align-items: center; margin-bottom: 12px;">
        <h2 style="margin: 0; color: #fff; border-left: 4px solid #ed8936; padding-left: 10px;">⭐ Favorites</h2>
        <div class="favorites-count">{len(favorites_list)} book{'s' if len(favorites_list) != 1 else ''}</div>
    </div>
    """
    
    return favorites_df, html, gr.update(visible=load_more_visible), count_html


# Replace the favorite action handler with this simple version:

# Simple favorite function
def handle_simple_favorite(book_id):
    """Simple function to handle favorites"""
    global favorites_list
    
    if book_id:
        # Find the book
        book_match = df[df['id'] == book_id]
        if not book_match.empty:
            book_data = book_match.iloc[0].to_dict()
            
            # Add to favorites if not already there
            if not any(fav['id'] == book_id for fav in favorites_list):
                favorites_list.append(book_data)
                print(f"✅ SIMPLE: Added '{book_data['title']}' to favorites")
                
                # Update display
                favorites_df, html, load_more_visible, header = update_favorites_display()
                return favorites_df, html, load_more_visible, header, "❤️ Added to favorites!"
    
    return favorites_state.value, favorites_container.value, favorites_load_more_btn.visible, favorites_header.value, "⚠️ Could not add to favorites"

# Connect the simple trigger
add_fav_trigger.click(
    handle_simple_favorite,
    inputs=[add_fav_book_id],
    outputs=[favorites_state, favorites_container, favorites_load_more_btn, favorites_header, feedback]
)

# ---------- Gradio UI ----------
with gr.Blocks(css="""
.books-section { border:1px solid #555; border-radius:12px; padding:16px; height:500px; overflow-y:auto; margin-bottom:20px; background:#222; }
.books-grid { display:grid; grid-template-columns:repeat(6,1fr); gap:16px; }
.book-card { background:#333; border-radius:12px; padding:10px; box-shadow:0 3px 10px rgba(0,0,0,0.5); cursor:pointer; text-align:left; transition:all 0.3s ease; border:1px solid #555; height:100%; display:flex; flex-direction:column; color:#eee; }
.book-card:hover { transform:translateY(-4px) scale(1.02); box-shadow:0 8px 20px rgba(0,0,0,0.7); border-color:#667eea; }
.book-image-container { position:relative; margin-bottom:10px; }
.book-card img { width:100%; height:180px; object-fit:cover; border-radius:8px; border:1px solid #666; }
.book-badge { position:absolute; top:8px; right:8px; background:rgba(102,126,234,0.9); color:white; padding:2px 6px; border-radius:10px; font-size:10px; font-weight:bold;}
.book-info { flex-grow:1; display:flex; flex-direction:column; gap:4px; }
.book-title { font-size:13px; font-weight:700; color:#fff; line-height:1.3; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; margin-bottom:2px; }
.book-authors { font-size:11px; color:#88c; font-weight:600; overflow:hidden; display:-webkit-box; -webkit-line-clamp:1; -webkit-box-orient:vertical; margin-bottom:3px;}
.book-rating { font-size:10px; color:#ffa500; margin-bottom:4px; }
.book-meta { display:flex; flex-direction:column; gap:2px; margin-top:auto; font-size:10px; color:#ccc; }

.load-more-btn { background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); color:white; border:none; padding:10px 25px; border-radius:20px; font-weight:600; cursor:pointer; transition:all 0.3s ease; box-shadow:0 4px 12px rgba(102,126,234,0.3); font-size:12px; }
.load-more-btn:hover { transform:translateY(-2px); box-shadow:0 6px 16px rgba(102,126,234,0.4); }

.favorite-btn { background:linear-gradient(135deg,#ed8936 0%,#dd6b20 100%); color:white; border:none; padding:12px 24px; border-radius:20px; font-weight:600; cursor:pointer; transition:all 0.3s ease; box-shadow:0 4px 12px rgba(237,137,54,0.3); font-size:14px; margin:10px 0; }
.favorite-btn:hover { transform:translateY(-2px); box-shadow:0 6px 16px rgba(237,137,54,0.4); }
.favorite-btn.remove { background:linear-gradient(135deg,#f56565 0%,#e53e3e 100%); }

.favorites-count { background:#ed8936; color:white; padding:4px 12px; border-radius:16px; font-size:12px; font-weight:600; margin-left:10px; }

.feedback-toast { position:fixed; top:20px; right:20px; background:#48bb78; color:white; padding:12px 20px; border-radius:8px; z-index:100000; box-shadow:0 4px 12px rgba(0,0,0,0.5); font-weight:600; }

/* Popup Styles */
.popup-overlay { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); backdrop-filter:blur(5px); z-index:99998; }
.popup-container { display:none; position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); background:#111; border-radius:16px; padding:24px; max-width:700px; width:90%; max-height:80vh; overflow-y:auto; box-shadow:0 20px 60px rgba(0,0,0,0.7); border:2px solid #667eea; z-index:99999; color:#eee; }
.popup-close { position:absolute; top:12px; right:16px; cursor:pointer; font-size:24px; font-weight:bold; color:#fff; background:#222; border-radius:50%; width:32px; height:32px; display:flex; align-items:center; justify-content:center; box-shadow:0 2px 6px rgba(0,0,0,0.5); transition:all 0.2s ease; }
.popup-close:hover { background:#667eea; color:white; }
.popup-content { line-height:1.6; }
.description-scroll { max-height:200px; overflow-y:auto; padding-right:8px; margin-top:10px; background:#222; border-radius:6px; padding:12px; border:1px solid #444; font-size:14px; line-height:1.5; }
.detail-stats { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin:15px 0; padding:15px; background:#1a1a1a; border-radius:8px; border:1px solid #333; }
.detail-stat { text-align:center; }
.detail-stat-value { font-size:16px; font-weight:bold; color:#667eea; }
.detail-stat-label { font-size:11px; color:#888; margin-top:4px; }
.favorite-action-section { margin-top:20px; padding-top:15px; border-top:2px solid #ed8936; text-align:center; }

/* Scrollbar */
.description-scroll::-webkit-scrollbar { width:6px; }
.description-scroll::-webkit-scrollbar-track { background:#333; border-radius:3px; }
.description-scroll::-webkit-scrollbar-thumb { background:#667eea; border-radius:3px; }
.description-scroll::-webkit-scrollbar-thumb:hover { background:#5a6fd8; }
""") as demo:

    gr.Markdown("# 📚 Dark Book Discovery Hub")
    gr.Markdown("### Explore our curated collection of amazing books")

    # Feedback component
    feedback = gr.HTML("")
    
    # ---------- Random Books Section ----------
    gr.Markdown("## 🎲 Random Books")
    random_books_container = gr.HTML(elem_classes="books-section")
    with gr.Row():
        random_load_more_btn = gr.Button("📚 Load More Random Books", elem_classes="load-more-btn")
        shuffle_btn = gr.Button("🔀 Shuffle Books", elem_classes="load-more-btn")

    # ---------- Popular Books Section ----------
    gr.Markdown("## 📈 Popular Books")
    popular_books_container = gr.HTML(elem_classes="books-section")
    popular_load_more_btn = gr.Button("📚 Load More Popular Books", elem_classes="load-more-btn")
    
    # ---------- Simple Favorites Trigger (using same pattern as other buttons) ----------
    with gr.Row(visible=False) as hidden_row:
        # Simple trigger that works like other buttons
        add_fav_trigger = gr.Button("Add Favorite Simple")
        add_fav_book_id = gr.Textbox(value="")


    # ---------- Favorites Section ----------
    with gr.Column():
        favorites_header = gr.HTML("""
        <div style="display: flex; align-items: center; margin-bottom: 12px;">
            <h2 style="margin: 0; color: #fff; border-left: 4px solid #ed8936; padding-left: 10px;">⭐ Favorites</h2>
            <div class="favorites-count">0 books</div>
        </div>
        """)
        favorites_container = gr.HTML(
            elem_classes="books-section", 
            value="<div style='text-align: center; padding: 40px; color: #888; font-size: 16px;'>No favorite books yet. Click the favorite button in book details to add some!</div>"
        )
        favorites_load_more_btn = gr.Button("📚 Load More Favorites", elem_classes="load-more-btn", visible=False)

    # ---------- VISIBLE Favorite Button (not hidden!) ----------
    gr.Markdown("### ⭐ Add to Favorites")
    with gr.Row():
        # Create a dropdown to select books
        book_choices = [(f"{book['title']} by {', '.join(book['authors'])}", book['id']) for _, book in df.iterrows()]
        book_dropdown = gr.Dropdown(
            choices=book_choices,
            label="Select a book to add to favorites",
            value=book_choices[0][1] if book_choices else None
        )
        favorite_btn = gr.Button("❤️ Add to Favorites", elem_classes="favorite-btn")

    # ---------- States ----------
    random_books_state = gr.State(df.sample(frac=1).reset_index(drop=True))
    random_display_state = gr.State(pd.DataFrame())
    random_index_state = gr.State(0)

    popular_books_state = gr.State(df.copy())
    popular_display_state = gr.State(pd.DataFrame())
    popular_index_state = gr.State(0)

    favorites_state = gr.State(pd.DataFrame())
    favorites_display_state = gr.State(pd.DataFrame())
    favorites_index_state = gr.State(0)

    # ---------- SIMPLE Functions ----------
    def load_more_random(loaded_books, display_books, page_idx):
        start = page_idx * BOOKS_PER_LOAD
        end = start + BOOKS_PER_LOAD
        new_books = loaded_books.iloc[start:end]
        if new_books.empty:
            return display_books, gr.update(value=build_books_grid_html(display_books)), gr.update(visible=False), page_idx
        combined = pd.concat([display_books,new_books],ignore_index=True)
        html = build_books_grid_html(combined)
        return combined, gr.update(value=html), gr.update(visible=True), page_idx+1

    def load_more_popular(loaded_books, display_books, page_idx):
        start = page_idx * BOOKS_PER_LOAD
        end = start + BOOKS_PER_LOAD
        new_books = loaded_books.iloc[start:end]
        if new_books.empty:
            return display_books, gr.update(value=build_books_grid_html(display_books)), gr.update(visible=False), page_idx
        combined = pd.concat([display_books,new_books],ignore_index=True)
        html = build_books_grid_html(combined)
        return combined, gr.update(value=html), gr.update(visible=True), page_idx+1

    def load_more_favorites(favorites_df, favorites_display, page_idx):
        start = page_idx * BOOKS_PER_LOAD
        end = start + BOOKS_PER_LOAD
        new_books = favorites_df.iloc[start:end]
        if new_books.empty:
            return favorites_display, gr.update(value=build_books_grid_html(favorites_display, True)), gr.update(visible=False), page_idx
        combined = pd.concat([favorites_display, new_books], ignore_index=True)
        html = build_books_grid_html(combined, True)
        return combined, gr.update(value=html), gr.update(visible=True), page_idx + 1

    def shuffle_random_books(loaded_books, display_books):
        shuffled = loaded_books.sample(frac=1).reset_index(drop=True)
        initial_books = shuffled.iloc[:BOOKS_PER_LOAD]
        html = build_books_grid_html(initial_books)
        return shuffled, initial_books, html, 1

    # SIMPLE FAVORITE FUNCTION - This WILL work!
    def handle_favorite_click(book_id):
        """Super simple function - just toggle the favorite"""
        print(f"🎯 Handling favorite for book: {book_id}")
        
        # Toggle favorite
        success, message = toggle_favorite(book_id)
        
        # Update display
        favorites_df, html, load_more_visible, header = update_favorites_display()
        
        # Create feedback
        feedback_html = f"""
        <div class="feedback-toast" style="background: {'#48bb78' if success else '#f56565'}">
            {message}
        </div>
        """
        
        return favorites_df, html, load_more_visible, header, feedback_html

    # ---------- Event Handlers ----------
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

    favorites_load_more_btn.click(
        load_more_favorites,
        [favorites_state, favorites_display_state, favorites_index_state],
        [favorites_display_state, favorites_container, favorites_load_more_btn, favorites_index_state]
    )

    # VISIBLE FAVORITE BUTTON HANDLER - This WILL work!
    favorite_btn.click(
        handle_favorite_click,
        inputs=[book_dropdown],
        outputs=[favorites_state, favorites_container, favorites_load_more_btn, favorites_header, feedback]
    )

    # ---------- Initial Load ----------
    def initial_load(df_):
        initial_books = df_.iloc[:BOOKS_PER_LOAD]
        html = build_books_grid_html(initial_books)
        return initial_books, html, 1

    # Initialize all sections
    random_display_state.value, random_books_container.value, random_index_state.value = initial_load(random_books_state.value)
    popular_display_state.value, popular_books_container.value, popular_index_state.value = initial_load(popular_books_state.value)
    favorites_state.value, favorites_container.value, favorites_index_state.value = pd.DataFrame(), favorites_container.value, 0

    # ---------- Popup with SIMPLE Favorite Integration ----------
# Replace the ENTIRE popup JavaScript section with this:

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

let currentBookId = null;
let originalScrollPosition = 0;

function escapeHtml(str) {
    return str ? String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;') : "";
}

function formatText(text) {
    if (!text) return 'No description available.';
    return text.replace(/\\n/g, '<br>');
}

// SIMPLE FAVORITES FUNCTION - Uses same pattern as other working buttons
function addToFavorites(bookId) {
    console.log('🎯 SIMPLE: Adding to favorites:', bookId);
    
    // Find the simple trigger button and input
    const buttons = Array.from(document.querySelectorAll('button'));
    const inputs = Array.from(document.querySelectorAll('input[type="text"]'));
    
    let triggerBtn = null;
    let bookIdInput = null;
    
    // Find the "Add Favorite Simple" button
    for (let btn of buttons) {
        if (btn.textContent.includes('Add Favorite Simple')) {
            triggerBtn = btn;
            break;
        }
    }
    
    // Find the book ID input (look for hidden inputs)
    for (let input of inputs) {
        const parent = input.closest('.row');
        if (parent && parent.style.display === 'none') {
            bookIdInput = input;
            break;
        }
    }
    
    if (triggerBtn && bookIdInput) {
        console.log('✅ Found components:', {triggerBtn, bookIdInput});
        
        // SIMPLE: Just set the value and click the button
        bookIdInput.value = bookId;
        
        // Small delay to ensure value is set
        setTimeout(() => {
            triggerBtn.click();
            console.log('✅ Button clicked successfully');
            
            // Show feedback
            showFeedback('❤️ Added to favorites!');
            
            // Close popup after a moment
            setTimeout(() => {
                closePopup();
            }, 1000);
            
        }, 100);
        
    } else {
        console.error('❌ Could not find components');
        console.log('Available buttons:', buttons.map(b => b.textContent));
        console.log('Available inputs:', inputs.map(i => i.value));
        showFeedback('Error: Could not add to favorites', false);
    }
}

function showFeedback(message, isSuccess = true) {
    const existing = document.querySelector('.feedback-toast');
    if (existing) existing.remove();
    
    const feedback = document.createElement('div');
    feedback.className = 'feedback-toast';
    feedback.style.background = isSuccess ? '#48bb78' : '#f56565';
    feedback.textContent = message;
    document.body.appendChild(feedback);
    
    setTimeout(() => {
        if (document.body.contains(feedback)) {
            document.body.removeChild(feedback);
        }
    }, 3000);
}

// Handle book card clicks (this part works fine)
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
    
    // Check if book is in favorites by looking for heart in title
    const isFavorite = card.querySelector('.book-title').textContent.includes('❤️');
    const favoriteButtonText = isFavorite ? '💔 Remove from Favorites' : '❤️ Add to Favorites';
    const favoriteButtonClass = isFavorite ? 'favorite-btn remove' : 'favorite-btn';
    
    content.innerHTML = `
        <div style="display: flex; gap: 20px; align-items: flex-start; margin-bottom: 20px;">
            <img src="${img}" style="width: 180px; height: auto; border-radius: 8px; object-fit: cover; box-shadow: 0 4px 12px rgba(0,0,0,0.5);">
            <div style="flex: 1;">
                <h2 style="margin: 0 0 12px 0; color: #fff; border-bottom: 2px solid #667eea; padding-bottom: 8px;">${escapeHtml(title)}</h2>
                <p style="margin: 0 0 8px 0; font-size: 14px;"><strong style="color: #88c;">Author(s):</strong> <span style="color: #667eea;">${escapeHtml(authors)}</span></p>
                <p style="margin: 0 0 8px 0; font-size: 14px;"><strong style="color: #88c;">Genres:</strong> <span style="color: #a78bfa;">${escapeHtml(genres)}</span></p>
                <p style="margin: 0 0 8px 0; font-size: 14px;"><strong style="color: #88c;">Rating:</strong> ${stars} <strong style="color: #ffa500;">${parseFloat(rating).toFixed(1)}</strong></p>
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
        
        <div style="margin-top: 16px;">
            <h3 style="margin: 0 0 10px 0; color: #fff; font-size: 16px; border-left: 3px solid #667eea; padding-left: 8px;">Description</h3>
            <div class="description-scroll">
                ${formatText(escapeHtml(desc))}
            </div>
        </div>
        
        <div class="favorite-action-section">
            <button class="${favoriteButtonClass}" onclick="addToFavorites('${currentBookId}')">
                ${favoriteButtonText}
            </button>
            <p style="margin: 8px 0 0 0; color: #888; font-size: 12px;">Click to ${isFavorite ? 'remove from' : 'add to'} your favorites collection</p>
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

// Make function globally available
window.addToFavorites = addToFavorites;
</script>
""")



        

demo.launch()