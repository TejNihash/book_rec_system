import ast
import pandas as pd
import gradio as gr
import random

# Load dataset
df = pd.read_csv("data_mini_books.csv")

# Convert authors/genres from string -> Python list
df["authors"] = df["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df["genres"] = df["genres"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# Lowercased helper columns
df["title_lower"] = df["title"].str.lower()
df["authors_lower"] = df["authors"].apply(lambda lst: [a.lower() for a in lst])
df["genres_lower"] = df["genres"].apply(lambda lst: [g.lower() for g in lst])

# Simple pagination
BOOKS_PER_PAGE = 12  # 2 rows of 6 books

def get_books_section(section_type, query="", page=0):
    """Get books for either section"""
    if section_type == "random":
        if query:
            query = query.strip().lower()
            mask_title = df["title_lower"].str.contains(query, na=False)
            mask_authors = df["authors_lower"].apply(lambda lst: any(query in a for a in lst))
            mask_genres = df["genres_lower"].apply(lambda lst: any(query in g for g in lst))
            filtered = df[mask_title | mask_authors | mask_genres]
            # For search results, return sequential pages
            start_idx = page * BOOKS_PER_PAGE
            return filtered.iloc[start_idx:start_idx + BOOKS_PER_PAGE]
        else:
            # True random sample
            return df.sample(n=BOOKS_PER_PAGE)
    else:  # popular
        start_idx = page * BOOKS_PER_PAGE
        return df.iloc[start_idx:start_idx + BOOKS_PER_PAGE]

def create_books_display(books_df, section_type):
    """Create the books display with proper sizing"""
    if books_df.empty:
        return "<div class='no-books'>No books found</div>"
    
    books_html = "".join([
        f"""
        <div class="book">
            <img src="{row['image_url']}" onerror="this.src='https://via.placeholder.com/150x220/667eea/white?text=No+Image'">
            <div class="book-info">
                <div class="title">{row['title']}</div>
                <div class="authors">by {', '.join(row['authors'])}</div>
                <div class="genres">{', '.join(row['genres'][:2])}</div>
            </div>
        </div>
        """ for _, row in books_df.iterrows()
    ])
    
    return f'<div class="books-display">{books_html}</div>'

# Simple handlers
def load_page(section_type, query, page):
    books = get_books_section(section_type, query, page)
    display = create_books_display(books, section_type)
    has_more = len(books) == BOOKS_PER_PAGE
    return display, page + 1, gr.update(visible=has_more)

def refresh_random(query):
    return load_page("random", query, 0)

def clear_search():
    random_display, random_page, random_btn = load_page("random", "", 0)
    popular_display, popular_page, popular_btn = load_page("popular", "", 0)
    return "", random_display, random_page, random_btn, popular_display, popular_page, popular_btn

with gr.Blocks(css="""
.books-display {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 15px;
    padding: 20px;
    max-height: 500px;
    overflow-y: auto;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    background: #fafafa;
}
.book {
    background: white;
    border-radius: 8px;
    padding: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    text-align: center;
}
.book img {
    width: 100%;
    height: 180px;
    object-fit: cover;
    border-radius: 4px;
    margin-bottom: 8px;
}
.book-info {
    padding: 0 5px;
}
.title {
    font-weight: bold;
    font-size: 12px;
    line-height: 1.3;
    margin-bottom: 4px;
    color: #2c3e50;
}
.authors {
    font-size: 10px;
    color: #666;
    margin-bottom: 3px;
}
.genres {
    font-size: 9px;
    color: #888;
    font-style: italic;
}
""") as demo:

    gr.Markdown("# 📚 Book Explorer")
    
    with gr.Row():
        search = gr.Textbox(placeholder="Search books...")
        clear_btn = gr.Button("Clear")
        refresh_btn = gr.Button("Refresh Random")
    
    with gr.Tab("Random Books"):
        random_display = gr.HTML()
        random_page = gr.State(0)
        load_random = gr.Button("Load More", visible=True)
    
    with gr.Tab("Popular Books"):
        popular_display = gr.HTML()
        popular_page = gr.State(0)
        load_popular = gr.Button("Load More", visible=True)

    # Event handlers
    search.submit(
        lambda q: load_page("random", q, 0),
        [search],
        [random_display, random_page, load_random]
    )
    
    load_random.click(
        lambda q, p: load_page("random", q, p),
        [search, random_page],
        [random_display, random_page, load_random]
    )
    
    load_popular.click(
        lambda p: load_page("popular", "", p),
        [popular_page],
        [popular_display, popular_page, load_popular]
    )
    
    refresh_btn.click(
        refresh_random,
        [search],
        [random_display, random_page, load_random]
    )
    
    clear_btn.click(clear_search, [], [
        search, random_display, random_page, load_random,
        popular_display, popular_page, load_popular
    ])

    demo.load(
        lambda: load_page("random", "", 0),
        [],
        [random_display, random_page, load_random]
    )
    demo.load(
        lambda: load_page("popular", "", 0),
        [],
        [popular_display, popular_page, load_popular]
    )

demo.launch()