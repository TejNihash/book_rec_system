# Add this simple favorites system - REPLACE your current favorites code with this:

# === SIMPLE FAVORITES SYSTEM ===
import json

# Global variable to store favorites (in production, use a database)
favorites_list = []

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
            
        # Return updated favorites display
        favorites_df = pd.DataFrame(favorites_list)
        html = build_books_grid_html(favorites_df)
        load_more_visible = len(favorites_list) > BOOKS_PER_LOAD
        
        return favorites_df, html, gr.update(visible=load_more_visible)
    
    return gr.State(), favorites_container, favorites_load_more_btn

def get_favorites_display():
    """Get current favorites for display"""
    favorites_df = pd.DataFrame(favorites_list)
    html = build_books_grid_html(favorites_df)
    load_more_visible = len(favorites_list) > BOOKS_PER_LOAD
    return html, gr.update(visible=load_more_visible)

# === FAVORITES SECTION (AT BOTTOM) ===
with gr.Column():
    favorites_header = gr.HTML("""
    <div style="display: flex; align-items: center; margin-bottom: 12px;">
        <h2 style="margin: 0; color: #2d3748; border-left: 4px solid #ed8936; padding-left: 10px;">⭐ Favorites</h2>
        <div class="favorites-count" id="favorites-count">0 books</div>
    </div>
    """)
    
    favorites_container = gr.HTML(
        elem_classes="books-section", 
        value="<div style='text-align: center; padding: 40px; color: #666;'>No favorite books yet. Click the ❤️ button in book details to add some!</div>"
    )
    
    with gr.Row():
        favorites_load_more_btn = gr.Button("📚 Load More Favorites", elem_classes="load-more-btn", visible=False)

# === HIDDEN COMPONENTS FOR FAVORITES ===
favorite_book_id = gr.Textbox(visible=False, label="Favorite Book ID")
add_favorite_btn = gr.Button("Add Favorite", visible=False)

# Connect the favorites button
add_favorite_btn.click(
    add_to_favorites_simple,
    inputs=[favorite_book_id],
    outputs=[favorites_state, favorites_container, favorites_load_more_btn]
)

# Update favorites count
def update_favorites_count():
    count = len(favorites_list)
    return gr.HTML.update(value=f"""
    <div style="display: flex; align-items: center; margin-bottom: 12px;">
        <h2 style="margin: 0; color: #2d3748; border-left: 4px solid #ed8936; padding-left: 10px;">⭐ Favorites</h2>
        <div class="favorites-count">{count} book{'s' if count != 1 else ''}</div>
    </div>
    """)

# Also update the favorites header when favorites change
add_favorite_btn.click(
    update_favorites_count,
    outputs=[favorites_header]
)

# === SIMPLIFIED POPUP JAVASCRIPT ===
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
    console.log('Adding to favorites:', bookId);
    
    // Find the hidden favorite components
    const favoriteIdInput = document.querySelector('input[aria-label="Favorite Book ID"]');
    const addFavoriteBtn = document.querySelector('button:contains("Add Favorite")');
    
    if (favoriteIdInput && addFavoriteBtn) {
        // Update the book ID
        favoriteIdInput.value = bookId;
        
        // Trigger change event
        const event = new Event('change', { bubbles: true });
        favoriteIdInput.dispatchEvent(event);
        
        // Click the add button
        addFavoriteBtn.click();
        
        console.log('Favorite added successfully');
    } else {
        console.log('Could not find favorite components');
    }
    
    // Show feedback
    showFeedback('❤️ Added to favorites!');
}

function showFeedback(message) {
    const feedback = document.createElement('div');
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

# Also add a simple test button to verify favorites work
with gr.Row():
    test_fav_btn = gr.Button("🧪 Test Favorites", visible=False)
    test_book_id = gr.Textbox(value="0", visible=False)

def test_add_favorite(book_id):
    """Test function to add a favorite"""
    return add_to_favorites_simple(book_id)

test_fav_btn.click(
    test_add_favorite,
    inputs=[test_book_id],
    outputs=[favorites_state, favorites_container, favorites_load_more_btn]
)