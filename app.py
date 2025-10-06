import ast
import pandas as pd
import gradio as gr
from gradio_modal import Modal
import random

# Load dataset
df = pd.read_csv("data_mini_books.csv")

# Convert string lists to Python lists
df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# Create searchable columns
df["title_lower"] = df["title"].str.lower()
df["authors_lower"] = df["authors"].apply(lambda lst: [a.lower() for a in lst])
df["genres_lower"] = df["genres"].apply(lambda lst: [g.lower() for g in lst])

# Simple settings
BOOKS_PER_LOAD = 12

def search_books(query, page=0):
    query = query.strip().lower()
    
    if query:
        mask_title = df["title_lower"].str.contains(query, na=False)
        mask_authors = df["authors_lower"].apply(lambda lst: any(query in a for a in lst))
        mask_genres = df["genres_lower"].apply(lambda lst: any(query in g for g in lst))
        filtered = df[mask_title | mask_authors | mask_genres]
    else:
        filtered = df.copy().sample(frac=1).reset_index(drop=True)
    
    start_idx = page * BOOKS_PER_LOAD
    end_idx = start_idx + BOOKS_PER_LOAD
    page_books = filtered.iloc[start_idx:end_idx]
    
    has_more = len(filtered) > end_idx
    return page_books, has_more

def get_popular_books(page=0):
    start_idx = page * BOOKS_PER_LOAD
    end_idx = start_idx + BOOKS_PER_LOAD
    page_books = df.iloc[start_idx:end_idx]
    
    has_more = len(df) > end_idx
    return page_books, has_more

def create_book_card(img_url, title, authors, genres, book_id):
    """Create a book card with click event"""
    return f"""
    <div class="book-card" onclick="bookClicked({book_id})">
        <img src="{img_url}" onerror="this.src='https://via.placeholder.com/150x220/667eea/white?text=No+Image'">
        <div class="book-info">
            <div class="title">{title}</div>
            <div class="authors">by {', '.join(authors)}</div>
            <div class="genres">{', '.join(genres[:2])}</div>
        </div>
    </div>
    """

def create_books_display(books_df, section_type="random"):
    """Create the books display grid"""
    if books_df.empty:
        return "<div class='no-books'>No books found</div>"
    
    books_html = "".join([
        create_book_card(row["image_url"], row["title"], row["authors"], row["genres"], row.name)
        for _, row in books_df.iterrows()
    ])
    
    return f'<div class="books-grid" id="{section_type}-books">{books_html}</div>'

def get_book_details(book_id):
    """Get detailed information for a specific book"""
    if book_id is None:
        return "Select a book to see details"
    
    try:
        book = df.loc[int(book_id)]
        
        title = book["title"]
        authors = ", ".join(book["authors"])
        genres = ", ".join(book["genres"])
        description = book.get("description", "No description available.")
        image_url = book["image_url"]
        
        year = book.get("published_year", "Unknown")
        rating = book.get("average_rating", "Not rated")
        pages = book.get("num_pages", "Unknown")
        
        details_html = f"""
        <div style="display: grid; grid-template-columns: 200px 1fr; gap: 20px; align-items: start;">
            <div>
                <img src="{image_url}" style="width: 100%; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);" 
                     onerror="this.src='https://via.placeholder.com/200x300/667eea/white?text=No+Image'">
            </div>
            <div>
                <h2 style="margin: 0 0 10px 0; color: #2c3e50;">{title}</h2>
                <p style="margin: 5px 0; color: #666;"><strong>Author(s):</strong> {authors}</p>
                <p style="margin: 5px 0; color: #666;"><strong>Genres:</strong> {genres}</p>
                <p style="margin: 5px 0; color: #666;"><strong>Published:</strong> {year}</p>
                <p style="margin: 5px 0; color: #666;"><strong>Rating:</strong> {rating}</p>
                <p style="margin: 5px 0; color: #666;"><strong>Pages:</strong> {pages}</p>
                <div style="margin-top: 20px;">
                    <h4 style="margin: 0 0 10px 0; color: #2c3e50;">Description</h4>
                    <p style="line-height: 1.6; color: #555; max-height: 300px; overflow-y: auto;">{description}</p>
                </div>
            </div>
        </div>
        """
        return details_html
    except:
        return "Book details not available"

def initial_state(query=""):
    random_books, random_has_more = search_books(query, 0)
    random_display = create_books_display(random_books, "random")
    
    popular_books, popular_has_more = get_popular_books(0)
    popular_display = create_books_display(popular_books, "popular")
    
    if query:
        results_text = f"🎲 Showing results for '{query}'"
    else:
        results_text = "🎲 Discover Random Books"
    
    return (
        random_display, popular_display, 
        1, 1,
        gr.update(visible=random_has_more), 
        gr.update(visible=popular_has_more),
        results_text,
        random_books,
        popular_books
    )

def load_more_random(query, current_page, current_books_df):
    new_books, has_more = search_books(query, current_page)
    
    if not new_books.empty:
        combined_books = pd.concat([current_books_df, new_books], ignore_index=True)
        combined_display = create_books_display(combined_books, "random")
        return combined_display, current_page + 1, gr.update(visible=has_more), combined_books
    else:
        return create_books_display(current_books_df, "random"), current_page, gr.update(visible=False), current_books_df

def load_more_popular(current_page, current_books_df):
    new_books, has_more = get_popular_books(current_page)
    
    if not new_books.empty:
        combined_books = pd.concat([current_books_df, new_books], ignore_index=True)
        combined_display = create_books_display(combined_books, "popular")
        return combined_display, current_page + 1, gr.update(visible=has_more), combined_books
    else:
        return create_books_display(current_books_df, "popular"), current_page, gr.update(visible=False), current_books_df

def refresh_random(query):
    random_books, random_has_more = search_books(query, 0)
    random_display = create_books_display(random_books, "random")
    return random_display, 1, gr.update(visible=random_has_more), random_books

def clear_search():
    return "", *initial_state("")

# Build the interface
with gr.Blocks() as demo:
    
    # Store the selected book ID
    selected_book_id = gr.State(value=None)
    
    # Book Details Modal
    with Modal(visible=False) as modal:
        gr.Markdown("## 📖 Book Details")
        book_details = gr.HTML()
        close_btn = gr.Button("Close", variant="secondary")
    
    gr.Markdown("# 📚 Book Explorer")
    
    with gr.Row():
        search_box = gr.Textbox(
            label="",
            placeholder="🔍 Search books by title, author, or genre...",
            scale=4
        )
        clear_btn = gr.Button("Clear", scale=1)
    
    # Random Books Section
    with gr.Column():
        with gr.Row():
            random_title = gr.Markdown("🎲 Discover Random Books")
            refresh_btn = gr.Button("🔄 Refresh")
        
        random_display = gr.HTML()
        with gr.Row():
            load_random_btn = gr.Button("📚 Load More Books", visible=True)
            random_page = gr.State(1)
            random_loaded_books = gr.State(pd.DataFrame())
    
    # Popular Books Section  
    with gr.Column():
        gr.Markdown("📚 Popular Books")
        popular_display = gr.HTML()
        with gr.Row():
            load_popular_btn = gr.Button("📚 Load More Books", visible=True)
            popular_page = gr.State(1)
            popular_loaded_books = gr.State(pd.DataFrame())

    # JavaScript for handling book clicks
    demo.load(
        None,
        None,
        None,
        js="""
        function bookClicked(bookId) {
            // This will trigger the Gradio event
            const event = new CustomEvent('book-selected', { detail: { bookId: bookId } });
            document.dispatchEvent(event);
        }
        
        // Listen for the custom event and update the Gradio component
        document.addEventListener('book-selected', function(e) {
            const bookId = e.detail.bookId;
            // Find the selected_book_id component and update it
            const inputs = document.querySelectorAll('input');
            for (let input of inputs) {
                if (input.style.display === 'none') {
                    input.value = bookId;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    break;
                }
            }
        });
        """
    )

    # When a book is selected, show the modal
    def on_book_selected(book_id):
        if book_id is not None:
            details = get_book_details(book_id)
            return gr.update(visible=True), details
        return gr.update(visible=False), "No book selected"

    # Event handlers
    search_box.submit(
        initial_state,
        [search_box],
        [random_display, popular_display, random_page, popular_page, load_random_btn, load_popular_btn, random_title, random_loaded_books, popular_loaded_books]
    )
    
    load_random_btn.click(
        load_more_random,
        [search_box, random_page, random_loaded_books],
        [random_display, random_page, load_random_btn, random_loaded_books]
    )
    
    load_popular_btn.click(
        load_more_popular,
        [popular_page, popular_loaded_books],
        [popular_display, popular_page, load_popular_btn, popular_loaded_books]
    )
    
    refresh_btn.click(
        refresh_random,
        [search_box],
        [random_display, random_page, load_random_btn, random_loaded_books]
    )
    
    clear_btn.click(
        clear_search,
        [],
        [search_box, random_display, popular_display, random_page, popular_page, load_random_btn, load_popular_btn, random_title, random_loaded_books, popular_loaded_books]
    )
    
    # When book is selected, show modal
    selected_book_id.change(
        on_book_selected,
        [selected_book_id],
        [modal, book_details]
    )
    
    # Close modal
    close_btn.click(
        lambda: (gr.update(visible=False), None),
        [],
        [modal, selected_book_id]
    )

    demo.load(
        initial_state,
        [search_box],
        [random_display, popular_display, random_page, popular_page, load_random_btn, load_popular_btn, random_title, random_loaded_books, popular_loaded_books]
    )

if __name__ == "__main__":
    demo.launch()