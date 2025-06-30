import streamlit as st
import requests
import datetime
import random
import re
from bs4 import BeautifulSoup

# ────────────────────────────────────────
# CONFIGURATION
# ────────────────────────────────────────
st.set_page_config(page_title="WikiHabit - Daily Learning", layout="centered")

# --- INDIC LANGUAGE SUPPORT: FONT INJECTION ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700&display=swap');
    html, body, [class*="st-"], [class*="css-"] {
        font-family: 'Noto Sans', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🧠 WikiHabit: Daily Learning Companion")

# --- INDIC LANGUAGE SUPPORT: EXPANDED LANGUAGE DICTIONARY ---
LANGUAGES = {
    # Indic Languages
    "हिन्दी (Hindi)": "hi",
    "বাংলা (Bengali)": "bn",
    "தமிழ் (Tamil)": "ta",
    "తెలుగు (Telugu)": "te",
    "मराठी (Marathi)": "mr",
    "ગુજરાતી (Gujarati)": "gu",
    "ಕನ್ನಡ (Kannada)": "kn",
    "മലയാളം (Malayalam)": "ml",
    "ਪੰਜਾਬੀ (Punjabi)": "pa",
    # Other Languages
    "English": "en",
    "Español (Spanish)": "es",
    "Deutsch (German)": "de",
    "Français (French)": "fr",
    "Italiano (Italian)": "it",
    "Português (Portuguese)": "pt",
}

# ────────────────────────────────────────
# SESSION STATE INITIALIZATION
# ────────────────────────────────────────
if "article_history" not in st.session_state: st.session_state.article_history = []
if "quiz_data" not in st.session_state: st.session_state.quiz_data = []
if "quiz_submitted" not in st.session_state: st.session_state.quiz_submitted = False
if "daily_word" not in st.session_state: st.session_state.daily_word = {}
if "daily_quote" not in st.session_state: st.session_state.daily_quote = {}
if "language_code" not in st.session_state: st.session_state.language_code = "en"

# ────────────────────────────────────────
# FUNCTIONS
# ────────────────────────────────────────

def fetch_wikiquote_quote(word, lang="en"):
    """
    Searches Wikiquote for a given word and returns a random quote from the page.
    This function is language-agnostic.
    """
    api_url = f"https://{lang}.wikiquote.org/w/api.php"
    headers = {'User-Agent': 'WikiHabit/1.6 (Robust Indic Support)'}
    try:
        search_params = {"action": "query", "format": "json", "list": "search", "srsearch": word}
        r_search = requests.get(api_url, params=search_params, headers=headers, timeout=5)
        r_search.raise_for_status()
        search_results = r_search.json().get("query", {}).get("search", [])
        if not search_results: return None

        page_title = search_results[0]["title"]
        parse_params = {"action": "parse", "page": page_title, "format": "json", "prop": "text", "disabletoc": True}
        r_parse = requests.get(api_url, params=parse_params, headers=headers, timeout=5)
        r_parse.raise_for_status()
        if "parse" not in r_parse.json(): return None

        html_content = r_parse.json()["parse"]["text"]["*"]
        soup = BeautifulSoup(html_content, 'html.parser')
        
        quotes = []
        for li in soup.find_all('li'):
            nested_ul = li.find('ul')
            if nested_ul and nested_ul.find('li'):
                quote_text = ''.join(li.find_all(string=True, recursive=False)).strip()
                source_text = nested_ul.find('li').get_text(strip=True)
                if len(quote_text) > 10:
                    quotes.append({"text": quote_text, "source": source_text})
        return random.choice(quotes) if quotes else None
    except (requests.exceptions.RequestException, KeyError, IndexError, TypeError):
        return None

def fetch_random_wiktionary_word(lang="en"):
    """
    Fetches a random word and its definition from Wiktionary.
    Enhanced version with fallback strategies and better error handling.
    """
    api_url = f"https://{lang}.wiktionary.org/w/api.php"
    headers = {'User-Agent': 'WikiHabit/1.7 (Enhanced Robustness)'}
    
    # First, try to get a word from a curated list for better success rate
    if lang == "en":
        fallback_words = [
            "serendipity", "ephemeral", "wanderlust", "solitude", "resilience",
            "harmony", "wisdom", "courage", "compassion", "gratitude",
            "adventure", "discovery", "knowledge", "creativity", "inspiration"
        ]
        
        # Try fallback words first (higher success rate)
        for word in random.sample(fallback_words, min(5, len(fallback_words))):
            try:
                parse_params = {"action": "parse", "page": word, "format": "json", "prop": "text", "disabletoc": True}
                r_parse = requests.get(api_url, params=parse_params, headers=headers, timeout=5)
                r_parse.raise_for_status()
                
                if "parse" not in r_parse.json():
                    continue
                    
                html_content = r_parse.json()["parse"]["text"]["*"]
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Look for any definition - be more flexible
                definition_found = False
                
                # Try multiple strategies to find definitions
                for strategy in range(3):
                    if strategy == 0:
                        # Strategy 1: Look for ordered lists
                        definition_lists = soup.find_all('ol')
                    elif strategy == 1:
                        # Strategy 2: Look for any lists
                        definition_lists = soup.find_all(['ol', 'ul'])
                    else:
                        # Strategy 3: Look for paragraphs with definitions
                        definition_lists = soup.find_all('p')
                    
                    for dl in definition_lists:
                        if strategy < 2:
                            items = dl.find_all('li')
                        else:
                            items = [dl]  # For paragraphs
                        
                        for item in items:
                            # Clean up the text
                            for tag in item.find_all(['ul', 'dl', 'table']):
                                tag.decompose()
                            
                            definition_text = item.get_text(strip=True)
                            
                            # More lenient filtering
                            if (len(definition_text) > 15 and 
                                len(definition_text) < 500 and
                                not any(skip in definition_text.lower() for skip in 
                                       ["wikipedia", "wiktionary", "see also", "external links", 
                                        "references", "further reading", "category:", "file:"])):
                                
                                return {"word": word.title(), "definition": definition_text}
                
            except (requests.exceptions.RequestException, KeyError, IndexError, TypeError):
                continue
    
    # If fallback words don't work, try random approach but with relaxed criteria
    for attempt in range(10):
        try:
            # Get a random page title
            random_params = {"action": "query", "format": "json", "list": "random", "rnnamespace": 0, "rnlimit": 1}
            r_random = requests.get(api_url, params=random_params, headers=headers, timeout=5)
            r_random.raise_for_status()
            random_title = r_random.json()["query"]["random"][0]["title"]
            
            # Skip if title looks like it won't have definitions
            if any(skip in random_title.lower() for skip in [":", "template", "category", "user", "file"]):
                continue
            
            # Parse the page
            parse_params = {"action": "parse", "page": random_title, "format": "json", "prop": "text", "disabletoc": True}
            r_parse = requests.get(api_url, params=parse_params, headers=headers, timeout=5)
            r_parse.raise_for_status()
            
            if "parse" not in r_parse.json():
                continue
                
            html_content = r_parse.json()["parse"]["text"]["*"]
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Try to find any reasonable definition
            all_text_elements = soup.find_all(['li', 'p', 'dd'])
            for element in all_text_elements:
                # Clean up
                for tag in element.find_all(['ul', 'dl', 'table', 'div']):
                    tag.decompose()
                
                text = element.get_text(strip=True)
                
                # Very lenient criteria - just needs to be reasonable length
                if (20 <= len(text) <= 300 and 
                    not any(skip in text.lower() for skip in 
                           ["wikipedia", "wiktionary", "see also", "external links", 
                            "references", "category:", "file:", "template:", "user:"])):
                    
                    return {"word": random_title, "definition": text}
                    
        except (requests.exceptions.RequestException, KeyError, IndexError, TypeError):
            continue
    
    # Ultimate fallback - return a generic inspiring message
    inspirational_words = {
        "en": {"word": "Learning", "definition": "The acquisition of knowledge or skills through experience, study, or by being taught. Every day is an opportunity to learn something new."},
        "hi": {"word": "शिक्षा", "definition": "ज्ञान या कौशल प्राप्त करने की प्रक्रिया। हर दिन कुछ नया सीखने का अवसर है।"},
        "es": {"word": "Aprendizaje", "definition": "La adquisición de conocimiento o habilidades a través de la experiencia, el estudio o la enseñanza."},
        "fr": {"word": "Apprentissage", "definition": "L'acquisition de connaissances ou de compétences par l'expérience, l'étude ou l'enseignement."},
        "de": {"word": "Lernen", "definition": "Der Erwerb von Wissen oder Fähigkeiten durch Erfahrung, Studium oder Unterricht."}
    }
    
    return inspirational_words.get(lang, inspirational_words["en"])

def fetch_wikipedia_article_details(title, lang="en"):
    """Fetches the canonical URL and title of a Wikipedia article."""
    api_url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {"action": "query", "format": "json", "titles": title, "prop": "info", "inprop": "url", "redirects": 1}
    headers = {'User-Agent': 'WikiHabit/1.6 (Robust Indic Support)'}
    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        pages = response.json()["query"]["pages"]
        page_id = next(iter(pages))
        if page_id == "-1": return None, f"Could not find an article titled '{title}'."
        article_info = pages[page_id]
        return {"title": article_info.get("title", title), "url": article_info.get("fullurl")}, None
    except requests.exceptions.RequestException as e:
        return None, f"Network error: {e}"

def fetch_wikipedia_summary(title, lang="en"):
    """Fetches a summary of a Wikipedia article."""
    formatted_title = title.strip().replace(" ", "_")
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{formatted_title}"
    headers = {'User-Agent': 'WikiHabit/1.6 (Robust Indic Support)'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("type") == "disambiguation": return f"'{title}' is a disambiguation page."
        return data.get("extract", f"No summary available for '{title}'.")
    except requests.exceptions.RequestException as e:
        return f"Couldn't fetch summary: {e}"

def generate_simple_quiz(text, num_questions=10):
    """Generates a fill-in-the-blank quiz. This works with Unicode characters automatically."""
    words = sorted(list(set([w.strip(".,;:()[]।") for w in text.split() if len(w.strip(".,;:()[]।")) > 3 and w.isalpha()])))
    if len(words) < 4: return []
    quiz_list, used_words = [], set()
    for _ in range(num_questions):
        available_words = [w for w in words if w not in used_words]
        if not available_words: break
        key_word = random.choice(available_words)
        used_words.add(key_word)
        question = text.replace(key_word, "_____", 1)
        options = {key_word}
        other_words = [w for w in words if w != key_word]
        if len(other_words) >= 3: options.update(random.sample(other_words, 3))
        else: options.update(other_words)
        options_list = list(options)
        random.shuffle(options_list)
        quiz_list.append({"question": question, "answer": key_word, "options": options_list})
    return quiz_list

# ────────────────────────────────────────
# SIDEBAR
# ────────────────────────────────────────
st.sidebar.title("⚙️ Settings / सेटिंग्स")
selected_language_name = st.sidebar.selectbox(
    "Choose your language / अपनी भाषा चुनें:",
    options=list(LANGUAGES.keys()),
    index=list(LANGUAGES.keys()).index(next(k for k, v in LANGUAGES.items() if v == st.session_state.language_code))
)
selected_lang_code = LANGUAGES[selected_language_name]

if selected_lang_code != st.session_state.language_code:
    st.session_state.language_code = selected_lang_code
    st.session_state.daily_word = {}
    st.session_state.daily_quote = {}
    st.session_state.article_history = []
    st.session_state.quiz_data = []
    st.session_state.quiz_submitted = False
    st.rerun()

st.sidebar.title("✨ Word of the Moment")
if st.sidebar.button("Get New Word") or not st.session_state.daily_word:
    with st.spinner("Fetching a new word..."):
        st.session_state.daily_word = fetch_random_wiktionary_word(lang=st.session_state.language_code)
        st.session_state.daily_quote = {}
        if st.session_state.daily_word.get("word") != "Error":
            st.session_state.daily_quote = fetch_wikiquote_quote(
                word=st.session_state.daily_word["word"],
                lang=st.session_state.language_code
            )

if st.session_state.daily_word:
    st.sidebar.markdown(f"**{st.session_state.daily_word.get('word', 'Word')}**")
    st.sidebar.write(st.session_state.daily_word.get('definition', 'No definition found.'))

if st.session_state.daily_quote:
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"> {st.session_state.daily_quote['text']}\n>\n> — *{st.session_state.daily_quote['source']}*")

# ────────────────────────────────────────
# MAIN APP FLOW
# ────────────────────────────────────────
st.header("📚 Add an Article to Your Reading")
search_query = st.text_input("Enter a Wikipedia article title:", placeholder="e.g., India / भारत")

if st.button("Fetch & Add Article"):
    if search_query.strip():
        with st.spinner(f"Verifying '{search_query}'..."):
            article_details, error = fetch_wikipedia_article_details(search_query, lang=st.session_state.language_code)
        if error:
            st.error(error)
        elif article_details:
            normalized_title = article_details["title"]
            if any(a['title'].lower() == normalized_title.lower() for a in st.session_state.article_history):
                st.warning(f"'{normalized_title}' is already in your list.")
            else:
                with st.spinner(f"Fetching summary for '{normalized_title}'..."):
                    summary = fetch_wikipedia_summary(normalized_title, lang=st.session_state.language_code)
                    if "Couldn't" in summary or "No summary" in summary or "disambiguation" in summary:
                        st.error(summary)
                    else:
                        st.session_state.article_history.append({"title": normalized_title, "url": article_details["url"], "summary": summary})
                        st.success(f"Added '{normalized_title}' to your list!")
                        st.session_state.quiz_data, st.session_state.quiz_submitted = [], False
    else:
        st.warning("Please enter an article title to fetch.")

if not st.session_state.article_history:
    st.info("Start by fetching an article in your chosen language!")

if st.session_state.article_history:
    st.write("---")
    st.write("### 📂 Articles Read Today")
    for i, article in enumerate(st.session_state.article_history):
        with st.expander(f"{i+1}. {article['title']}"):
            st.markdown(f"**[Read full article on Wikipedia]({article['url']})**")
            st.write(article["summary"])

    if st.button("🧠 Generate Quiz from My Articles"):
        full_text = " ".join([a["summary"] for a in st.session_state.article_history])
        if full_text.strip():
            with st.spinner("Generating your quiz..."):
                st.session_state.quiz_data = generate_simple_quiz(full_text)
                st.session_state.quiz_submitted = False
                if not st.session_state.quiz_data: st.warning("Could not generate a quiz from the articles.")
        else:
            st.warning("The article summaries are empty.")

if st.session_state.quiz_data and not st.session_state.quiz_submitted:
    st.write("---")
    st.write("## 🎯 Daily Quiz")
    st.info("Answer all questions and then click 'Submit' at the bottom.")
    with st.form("quiz_form"):
        user_answers = [st.radio(f"**Q{i+1}:** {q['question']}", q['options'], key=f"quiz_{i}") for i, q in enumerate(st.session_state.quiz_data)]
        if st.form_submit_button("Submit & See Results"):
            st.session_state.quiz_submitted = True
            st.session_state.user_answers = user_answers
            st.rerun()

if st.session_state.quiz_submitted:
    st.write("---")
    st.write("## 🏁 Quiz Results")
    score = 0
    total = len(st.session_state.quiz_data)
    user_answers = st.session_state.get('user_answers', [])
    for i, quiz in enumerate(st.session_state.quiz_data):
        if i < len(user_answers) and user_answers[i] == quiz['answer']:
            score += 1
    st.subheader(f"Your Score: {score} / {total}")
    if total > 0:
        score_percent = score / total
        st.progress(score_percent)
        if score_percent == 1.0:
            st.balloons()
            st.success("🎉 Perfect Score! Well done!")
    st.write("---")
    st.write("### Detailed Review:")
    for i, quiz in enumerate(st.session_state.quiz_data):
        st.markdown(f"**Q{i+1}:** {quiz['question'].replace('_____', f'**_{quiz["answer"]}_**')}")
        user_ans = user_answers[i] if i < len(user_answers) else "No answer"
        if user_ans == quiz['answer']:
            st.success(f"✅ Correct! You answered: **{user_ans}**")
        else:
            st.error(f"❌ Incorrect. You answered: **{user_ans}**. Correct answer: **{quiz['answer']}**")
        st.markdown("---")