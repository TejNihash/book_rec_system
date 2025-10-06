import ast
import pandas as pd
import gradio as gr
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

# Add ID column
if "id" not in df.columns:
    df["id"] = df.index.astype(str)

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

def create_book_component(book_row):
    """Create a book card using Gradio components"""
    with gr.Column(visible=True) as book_card:
        with gr.Row():
            # Book cover
            gr.HTML(f"""
                <img src="{book_row['image_url']}" 
                     style="width: 80px; height: 120px; object-fit: cover; border-radius: 4px;"
                     onerror="this.src='https://via.placeholder.com/80x120/667eea/white?text=No+Image'">
            """)
            
            # Book info
            with gr.Column(scale=2):
                gr.Markdown(f"**{book_row['title']}**")
                gr.Markdown(f"by {', '.join(book_row['authors'])}")
                gr.Markdown(f"*{', '.join(book_row['genres'][:2])}*")
        
        # View Details button
        view_btn = gr.Button("View Details", size="sm")
    
    return book_card, view_btn, book_row["id"]

def create_book_details(book_row):
    """Create expanded book details view"""
    with gr.Column(visible=False) as book_details:
        with gr.Row():
            # Large cover
            gr.HTML(f"""
                <img src="{book_row['image_url']}" 
                     style="width: 150px; height: 225px; object-fit: cover; border-radius: 8px;"
                     onerror="this.src='https://via.placeholder.com/150x225/667eea/white?text=No+Image'">
            """)
            
            # Detailed info
            with gr.Column():
                gr.Markdown(f"# {book_row['title']}")
                gr.Markdown(f"### by {', '.join(book_row['authors'])}")
                
                with gr.Row():
                    gr.Markdown(f"**Genres:** {', '.join(book_row['genres'])}")
                    gr.Markdown(f"**Year:** {book_row.get('published_year', 'Unknown')}")
                    gr.Markdown(f"**Rating:** {book_row.get('average_rating', 'Not rated')}")
                    gr.Markdown(f"**Pages:** {book_row.get('num_pages', 'Unknown')}")
                
                gr.Markdown(f"**Description:**\n{book_row.get('description', 'No description available.')}")
        
        # Back button
        back_btn = gr.Button("← Back to List", size="sm")
    
    return book_details, back_btn

# State management
random_loaded_books = gr.State(pd.DataFrame())
popular_loaded_books = gr.State(pd.DataFrame())
expanded_book_id = gr.State(None)

def initial_state(query=""):
    random_books, random_has_more = search_books(query, 0)
    popular_books, popular_has_more = get_popular_books(0)
    
    if query:
        results_text = f"🎲 Showing results for '{query}'"
    else:
        results_text = "🎲 Discover Random Books"
    
    return (
        random_books, popular_books,
        1, 1,
        gr.update(visible=random_has_more), 
        gr.update(visible=popular_has_more),
        results_text,
        random_books,
        popular_books,
        None  # expanded_book_id
    )

def load_more_random(query, current_page, current_books_df):
    new_books, has_more = search_books(query, current_page)
    
    if not new_books.empty:
        combined_books = pd.concat([current_books_df, new_books], ignore_index=True)
        return combined_books, current_page + 1, gr.update(visible=has_more), combined_books
    else:
        return current_books_df, current_page, gr.update(visible=False), current_books_df

def load_more_popular(current_page, current_books_df):
    new_books, has_more = get_popular_books(current_page)
    
    if not new_books.empty:
        combined_books = pd.concat([current_books_df, new_books], ignore_index=True)
        return combined_books, current_page + 1, gr.update(visible=has_more), combined_books
    else:
        return current_books_df, current_page, gr.update(visible=False), current_books_df

def refresh_random(query):
    random_books, random_has_more = search_books(query, 0)
    return random_books, 1, gr.update(visible=random_has_more), random_books

def clear_search():
    return "", *initial_state("")

# Build the interface
with gr.Blocks(css="""
    .book-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .book-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    .book-details {
        border: 2px solid #667eea;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        background: #f8faff;
    }
    .books-container {
        max-height: 600px;
        overflow-y: auto;
        padding: 10px;
    }
    .container {
        border: 1px solid #ddd;
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
        background: white;
    }
    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
    }
""") as demo:

    gr.Markdown("# 📚 Book Explorer")
    
    # Hidden state
    expanded_book_id = gr.State(None)
    
    with gr.Row():
        search_box = gr.Textbox(
            label="",
            placeholder="🔍 Search books by title, author, or genre...",
            scale=4
        )
        clear_btn = gr.Button("Clear", scale=1)
    
    # Store references to book components
    random_book_refs = gr.State([])
    popular_book_refs = gr.State([])
    
    # Random Books Section
    with gr.Column(visible=True) as random_section:
        with gr.Row(elem_classes="section-header"):
            random_title = gr.Markdown("🎲 Discover Random Books")
            refresh_btn = gr.Button("🔄 Refresh")
        
        random_display = gr.Column(elem_classes="books-container")
        
        with gr.Row():
            load_random_btn = gr.Button("📚 Load More Books", visible=True)
            random_page = gr.State(1)
            random_loaded_books = gr.State(pd.DataFrame())
    
    # Popular Books Section  
    with gr.Column(visible=True) as popular_section:
        with gr.Row(elem_classes="section-header"):
            gr.Markdown("📚 Popular Books")
        
        popular_display = gr.Column(elem_classes="books-container")
        
        with gr.Row():
            load_popular_btn = gr.Button("📚 Load More Books", visible=True)
            popular_page = gr.State(1)
            popular_loaded_books = gr.State(pd.DataFrame())
    
    # Expanded book view (initially hidden)
    with gr.Column(visible=False) as expanded_view:
        gr.Markdown("## 📖 Book Details")
        expanded_content = gr.Column()
        back_btn = gr.Button("← Back to Books")
    
    def create_book_components(books_df, container, section_type):
        """Create book components in the given container"""
        components = []
        
        with container:
            # Clear previous content
            container.__init__()
            
            for _, book in books_df.iterrows():
                # Create book card
                book_card, view_btn, book_id = create_book_component(book)
                components.append((book_card, view_btn, book_id))
                
                # Create details view (hidden initially)
                book_details, back_btn_details = create_book_details(book)
                
                # Connect view button to show details
                def create_view_handler(book_id_val, details_component, card_component, section_comp, expanded_comp):
                    def handler():
                        # Hide all book cards, show details
                        updates = [gr.update(visible=False) for _ in section_comp] + [gr.update(visible=True)]
                        return updates + [book_id_val]
                    return handler
                
                view_btn.click(
                    fn=lambda bid=book_id: (gr.update(visible=False), gr.update(visible=True), bid),
                    outputs=[random_section if section_type == "random" else popular_section, expanded_view, expanded_book_id]
                )
        
        return components
    
    def show_book_details(book_id):
        """Show the expanded book details view"""
        if book_id is None:
            return gr.update(visible=True), gr.update(visible=False), None
        
        return gr.update(visible=False), gr.update(visible=True), book_id
    
    def back_to_list():
        """Return to book list view"""
        return gr.update(visible=True), gr.update(visible=False), None
    
    # Connect back button
    back_btn.click(
        back_to_list,
        outputs=[random_section, expanded_view, expanded_book_id]
    )
    
    # Search handler
    def handle_search(query):
        random_books, popular_books, r_page, p_page, r_has_more, p_has_more, r_title, r_loaded, p_loaded, _ = initial_state(query)
        
        # Create book components
        random_comps = create_book_components(random_books, random_display, "random")
        popular_comps = create_book_components(popular_books, popular_display, "popular")
        
        return r_page, p_page, r_has_more, p_has_more, r_title, r_loaded, p_loaded
    
    search_box.submit(
        handle_search,
        [search_box],
        [random_page, popular_page, load_random_btn, load_popular_btn, random_title, random_loaded_books, popular_loaded_books]
    )
    
    # Initial load
    def load_initial():
        random_books, popular_books, r_page, p_page, r_has_more, p_has_more, r_title, r_loaded, p_loaded, _ = initial_state()
        
        # Create initial book components
        create_book_components(random_books, random_display, "random")
        create_book_components(popular_books, popular_display, "popular")
        
        return r_page, p_page, r_has_more, p_has_more, r_title, r_loaded, p_loaded
    
    demo.load(
        load_initial,
        [],
        [random_page, popular_page, load_random_btn, load_popular_btn, random_title, random_loaded_books, popular_loaded_books]
    )

demo.launch()