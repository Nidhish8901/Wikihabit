import streamlit as st
import requests
import random
import re
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
st.set_page_config(page_title="WikiHabit - Smart Quiz", layout="centered")
st.markdown("""<style>@import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700&display=swap'); html, body, [class*="st-"], [class*="css-"] {font-family: 'Noto Sans', sans-serif;}</style>""", unsafe_allow_html=True)
st.title("🧠 WikiHabit: Smart Quiz Companion")
st.subheader("Generates a quiz directly from Wikipedia articles")

# --- LANGUAGE & SESSION STATE SETUP ---
LANGUAGES = {
    "English": "en", "हिन्दी (Hindi)": "hi", "Español (Spanish)": "es",
    "Français (French)": "fr", "Deutsch (German)": "de", "Português (Portuguese)": "pt",
    "Italiano (Italian)": "it", "বাংলা (Bengali)": "bn", "தமிழ் (Tamil)": "ta",
    "తెలుగు (Telugu)": "te", "मराठी (Marathi)": "mr", "ગુજરાતી (Gujarati)": "gu",
    "ಕನ್ನಡ (Kannada)": "kn", "മലയാളം (Malayalam)": "ml", "ਪੰਜਾਬੀ (Punjabi)": "pa",
}

if "article_history" not in st.session_state: st.session_state.article_history = []
if "quiz_data" not in st.session_state: st.session_state.quiz_data = []
if "quiz_submitted" not in st.session_state: st.session_state.quiz_submitted = False
if "daily_word" not in st.session_state: st.session_state.daily_word = {}
if "daily_quote" not in st.session_state: st.session_state.daily_quote = {}
if "language_code" not in st.session_state: st.session_state.language_code = "en"
if "disambiguation_options" not in st.session_state: st.session_state.disambiguation_options = []
if "active_quiz_title" not in st.session_state: st.session_state.active_quiz_title = ""

# --- FUNCTIONS ---

def generate_stubborn_quiz(text, num_questions=5):
    """
    A robust, case-correct quiz generator that always produces logical options.
    """
    if not text or not text.strip(): return []
    quiz_list = []; stop_words_lower = set("a an the is are was were of in on at for with by and or but".split())
    words = text.split(); cleaned_words = [re.sub(r'^[^\w\s-]+|[^\w\s-]+$', '', w) for w in words if w]
    unique_words = sorted(list(set(w for w in cleaned_words if len(w) > 3)), key=len, reverse=True)
    significant_words_lower = {w.lower() for w in unique_words if w.lower() not in stop_words_lower}
    sentences = re.split(r'(?<=[.?!।])\s+', text); valid_sentences = [s.strip() for s in sentences if len(s.split()) > 4]; random.shuffle(valid_sentences)
    used_answers_lower = set()
    for sentence in valid_sentences:
        if len(quiz_list) >= num_questions: break
        words_in_sentence = [re.sub(r'^[^\w\s-]+|[^\w\s-]+$', '', w) for w in sentence.split() if w]
        possible_answers = [w for w in words_in_sentence if w.lower() in significant_words_lower and w.lower() not in used_answers_lower]
        if not possible_answers: continue
        answer = random.choice(possible_answers); answer_lower = answer.lower(); used_answers_lower.add(answer_lower)
        question_text = sentence.replace(answer, "_____", 1)
        options = {answer}; distractor_pool = [w for w in unique_words if w.lower() != answer_lower and w.lower() in significant_words_lower]
        num_distractors = min(3, len(distractor_pool))
        if num_distractors > 0: options.update(random.sample(distractor_pool, num_distractors))
        if len(options) >= 2:
            options_list = list(options); random.shuffle(options_list)
            quiz_list.append({"question": question_text, "options": options_list, "answer": answer})
    if not quiz_list and len(cleaned_words) > 1:
        desperation_pool = list(set(w for w in cleaned_words if len(w) > 0))
        if len(desperation_pool) >= 2:
            answer = random.choice(desperation_pool); question = text.replace(answer, "_____", 1)
            options = {answer}; other_options = [w for w in desperation_pool if w != answer]
            options.update(random.sample(other_options, min(3, len(other_options))))
            options_list = list(options); random.shuffle(options_list)
            quiz_list.append({"question": question, "options": options_list, "answer": answer})
    return quiz_list

def fetch_wikiquote_quote(word, lang="en"):
    api_url = f"https://{lang}.wikiquote.org/w/api.php"; headers = {'User-Agent': 'WikiHabit/4.8 (HardcodeWordFix)'}
    try:
        search_params = {"action": "query", "format": "json", "list": "search", "srsearch": word}; r_search = requests.get(api_url, params=search_params, headers=headers, timeout=5); r_search.raise_for_status()
        search_results = r_search.json().get("query", {}).get("search", []);
        if not search_results: return None
        page_title = search_results[0]["title"]; parse_params = {"action": "parse", "page": page_title, "format": "json", "prop": "text", "disabletoc": True}
        r_parse = requests.get(api_url, params=parse_params, headers=headers, timeout=5); r_parse.raise_for_status()
        if "parse" not in r_parse.json(): return None
        html_content = r_parse.json()["parse"]["text"]["*"]; soup = BeautifulSoup(html_content, 'html.parser'); quotes = []
        for li in soup.find_all('li'):
            nested_ul = li.find('ul')
            if nested_ul and nested_ul.find('li'):
                quote_text = ''.join(li.find_all(string=True, recursive=False)).strip(); source_text = nested_ul.find('li').get_text(strip=True)
                if len(quote_text) > 10: quotes.append({"text": quote_text, "source": source_text})
        return random.choice(quotes) if quotes else None
    except: return None

# --- FOOLPROOF, 100% RELIABLE WORD OF THE DAY FUNCTION ---
def fetch_random_wiktionary_word(lang="en"):
    """
    This function is now 100% reliable.
    It uses a hard-coded dictionary for English and Spanish, ensuring no network failures or bad data.
    It falls back to the old web-scraping method only for other languages.
    """
    # TIER 1: HARD-CODED, GUARANTEED WORD LISTS
    word_bank = {
        "en": {
            "Serendipity": "The occurrence of events by chance in a happy or beneficial way.",
            "Ephemeral": "Lasting for a very short time.",
            "Luminous": "Emitting or reflecting bright light; shining.",
            "Resilience": "The capacity to recover quickly from difficulties; toughness.",
            "Eloquent": "Fluent or persuasive in speaking or writing.",
            "Mellifluous": "A sound that is sweet and pleasant to hear.",
            "Sonder": "The realization that each random passerby is living a life as vivid and complex as your own.",
            "Ineffable": "Too great or extreme to be expressed or described in words.",
            "Solitude": "The state of being alone, often by choice, and finding it peaceful.",
            "Wanderlust": "A strong desire to travel and explore the world."
        },
        "es": {
            "Serendipia": "El descubrimiento o hallazgo afortunado e inesperado que se produce de manera accidental.",
            "Efímero": "Que dura por un período de tiempo muy corto.",
            "Luminoso": "Que emite o refleja luz brillante; resplandeciente.",
            "Resiliencia": "La capacidad de adaptarse y recuperarse de la adversidad.",
            "Elocuente": "Que se expresa de manera fluida y persuasiva al hablar o escribir."
        }
        # Add more languages here as needed
    }

    if lang in word_bank:
        word, definition = random.choice(list(word_bank[lang].items()))
        return {"word": word, "definition": definition}

    # TIER 2: FALLBACK TO WEB-SCRAPING FOR OTHER LANGUAGES
    headers = {'User-Agent': 'WikiHabit/4.8 (HardcodeWordFix)'}
    api_url = f"https://{lang}.wiktionary.org/w/api.php"
    for _ in range(10):
        try:
            random_params = {"action": "query", "format": "json", "list": "random", "rnnamespace": 0, "rnlimit": 1}
            r_random = requests.get(api_url, params=random_params, headers=headers, timeout=5)
            r_random.raise_for_status()
            random_title = r_random.json()["query"]["random"][0]["title"]
            if any(skip in random_title.lower() for skip in [":", "template", "category", "user", "file", "appendix:"]): continue
            parse_params = {"action": "parse", "page": random_title, "format": "json", "prop": "text", "disabletoc": True}
            r_parse = requests.get(api_url, params=parse_params, headers=headers, timeout=5); r_parse.raise_for_status()
            if "parse" not in r_parse.json(): continue
            html_content = r_parse.json()["parse"]["text"]["*"]; soup = BeautifulSoup(html_content, 'html.parser')
            all_text_elements = soup.find_all(['li', 'p', 'dd'])
            for element in all_text_elements:
                for tag in element.find_all(['ul', 'dl', 'table', 'div']): tag.decompose()
                text = element.get_text(strip=True)
                if (20 <= len(text) <= 300 and not any(skip in text.lower() for skip in ["wikipedia", "wiktionary", "see also", "references", "category:", "file:"])):
                    return {"word": random_title.title(), "definition": text}
        except: continue
            
    # TIER 3: ULTIMATE FALLBACK IF ALL ELSE FAILS
    return {"word": "Learning", "definition": "The acquisition of knowledge or skills through experience, study, or by being taught."}

def fetch_wikipedia_summary(title, lang="en"):
    formatted_title = title.strip().replace(" ", "_"); url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{formatted_title}"; headers = {'User-Agent': 'WikiHabit/4.8 (HardcodeWordFix)'}
    try:
        response = requests.get(url, headers=headers, timeout=10); response.raise_for_status(); data = response.json()
        return data
    except requests.exceptions.RequestException as e: return {"error": f"Couldn't fetch summary: {e}"}

def fetch_disambiguation_links(title, lang="en"):
    api_url = f"https://{lang}.wikipedia.org/w/api.php"; params = {"action": "parse", "page": title, "prop": "links", "format": "json", "pllimit": "max"}; headers = {'User-Agent': 'WikiHabit/4.8 (HardcodeWordFix)'}
    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=10); response.raise_for_status()
        links = response.json().get("parse", {}).get("links", []); return [link["*"] for link in links if ":" not in link["*"] and "disambiguation" not in link["*"].lower()]
    except (requests.RequestException, KeyError): return []

st.sidebar.title("⚙️ Settings / सेटिंग्स")
selected_language_name = st.sidebar.selectbox("Choose your language / अपनी भाषा चुनें:", options=list(LANGUAGES.keys()), index=list(LANGUAGES.keys()).index(next(k for k, v in LANGUAGES.items() if v == st.session_state.language_code)))
selected_lang_code = LANGUAGES[selected_language_name]
if selected_lang_code != st.session_state.language_code:
    st.session_state.language_code = selected_lang_code; st.session_state.daily_word = {}; st.session_state.daily_quote = {}; st.session_state.article_history = []; st.session_state.quiz_data = []; st.session_state.quiz_submitted = False; st.rerun()

st.sidebar.title("✨ Word of the Moment")
if st.sidebar.button("Get New Word") or not st.session_state.daily_word:
    # This call is now 100% reliable for English and Spanish
    st.session_state.daily_word = fetch_random_wiktionary_word(lang=st.session_state.language_code)
    st.session_state.daily_quote = {};
    if st.session_state.daily_word: st.session_state.daily_quote = fetch_wikiquote_quote(word=st.session_state.daily_word["word"], lang=st.session_state.language_code)

if st.session_state.daily_word: st.sidebar.markdown(f"**{st.session_state.daily_word.get('word', 'Word')}**"); st.sidebar.write(st.session_state.daily_word.get('definition', 'No definition found.'))
if st.session_state.daily_quote: st.sidebar.markdown("---"); st.sidebar.markdown(f"> {st.session_state.daily_quote['text']}\n>\n> — *{st.session_state.daily_quote['source']}*")

st.header("📚 Add an Article to Your Reading")

def process_article_search(query, lang_code):
    st.session_state.disambiguation_options = []
    st.session_state.active_quiz_title = ""
    with st.spinner(f"Searching for '{query}'..."):
        summary_data = fetch_wikipedia_summary(query, lang=lang_code)
        if summary_data.get("title") == "Not found.": st.error(f"Could not find an article titled '{query}'. Please try a different title."); return
        if summary_data.get("type") == "disambiguation":
            st.warning(f"'{query}' is a disambiguation page. Please choose a specific topic:"); st.session_state.disambiguation_options = fetch_disambiguation_links(summary_data.get("title"), lang=lang_code); return
        title = summary_data.get("title", query)
        if any(a['title'].lower() == title.lower() for a in st.session_state.article_history): st.warning(f"'{title}' is already in your reading list."); return
        article = {"title": title, "url": summary_data.get("content_urls", {}).get("desktop", {}).get("page", ""), "summary": summary_data.get("extract", "No summary available.")}
        st.session_state.article_history.insert(0, article); st.success(f"Added '{title}' to your list!");
        st.session_state.quiz_data = []; st.session_state.quiz_submitted = False

with st.form(key="search_form"):
    search_query = st.text_input("Enter a Wikipedia article title:", placeholder="e.g., India / भारत")
    submitted = st.form_submit_button("Fetch & Add Article")
    if submitted:
        if search_query.strip(): process_article_search(search_query, st.session_state.language_code)
        else: st.warning("Please enter an article title.")

if st.session_state.disambiguation_options:
    st.write("---"); cols = st.columns(3)
    for i, option in enumerate(st.session_state.disambiguation_options):
        with cols[i % 3]:
            if st.button(option, key=f"disamb_option_{i}"):
                process_article_search(option, st.session_state.language_code); st.rerun()

if not st.session_state.article_history and not st.session_state.disambiguation_options: st.info("Start by fetching an article in your chosen language!")

if st.session_state.article_history:
    st.write("---"); st.write("### 📂 Articles Read Today")
    for i, article in enumerate(st.session_state.article_history):
        with st.expander(f"{i+1}. {article['title']}", expanded=(i == 0)):
            st.markdown(f"**[Read full article on Wikipedia]({article['url']})**"); st.write(article["summary"])
            if st.button("🧠 Generate Quiz for this Article", key=f"quiz_btn_{article['title']}"):
                with st.spinner(f"Generating quiz for '{article['title']}'..."):
                    st.session_state.quiz_data = generate_stubborn_quiz(article['summary'], num_questions=5)
                    st.session_state.quiz_submitted = False
                    st.session_state.active_quiz_title = article['title']

if st.session_state.quiz_data and st.session_state.active_quiz_title:
    st.write("---"); st.write(f"## 🎯 Daily Quiz: {st.session_state.active_quiz_title}")
    st.info("Answer all questions and then click 'Submit' at the bottom.")
    with st.form("quiz_form"):
        user_answers = [st.radio(f"**Q{i+1}:** {q['question']}", q['options'], key=f"quiz_{i}") for i, q in enumerate(st.session_state.quiz_data)]
        if st.form_submit_button("Submit & See Results"):
            st.session_state.quiz_submitted = True; st.session_state.user_answers = user_answers; st.rerun()

if st.session_state.quiz_submitted:
    st.write("---"); st.write(f"## 🏁 Quiz Results: {st.session_state.active_quiz_title}")
    score = 0; total = len(st.session_state.quiz_data); user_answers = st.session_state.get('user_answers', [])
    for i, quiz in enumerate(st.session_state.quiz_data):
        if i < len(user_answers) and user_answers[i] == quiz['answer']: score += 1
    st.subheader(f"Your Score: {score} / {total}")
    if total > 0:
        score_percent = score / total; st.progress(score_percent)
        if score_percent == 1.0: st.balloons(); st.success("🎉 Perfect Score! Well done!")
    st.write("---"); st.write("### Detailed Review:")
    for i, quiz in enumerate(st.session_state.quiz_data):
        original_answer = quiz['answer']
        question_with_answer = quiz['question'].replace('_____', f"**_{original_answer}_**")
        st.markdown(f"**Q{i+1}:** {question_with_answer}")
        user_ans = user_answers[i] if i < len(user_answers) else "No answer"
        if user_ans == original_answer: st.success(f"✅ Correct! You answered: **{user_ans}**")
        else: st.error(f"❌ Incorrect. You answered: **{user_ans}**. Correct answer: **{original_answer}**")
        st.markdown("---")
