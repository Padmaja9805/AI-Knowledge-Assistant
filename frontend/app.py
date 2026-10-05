import streamlit as st
import requests
from urllib.parse import quote
import os
from dotenv import load_dotenv

# ============================================================
# CONFIG
# ============================================================

load_dotenv()

try:
    configured_api_url = st.secrets.get("API_URL")
except FileNotFoundError:
    configured_api_url = None

API_URL = (
    configured_api_url
    or os.getenv("API_URL")
    or "http://127.0.0.1:8000"
).strip().rstrip("/")
if not API_URL.startswith(("http://", "https://")):
    API_URL = f"https://{API_URL}"

st.set_page_config(
    page_title="AI Knowledge Assistant",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>
    :root {
        color-scheme: light;
        --background-color: #f5f8f5;
        --secondary-background-color: #ffffff;
        --text-color: #17231f;
        --primary-color: #197a5b;
        --ink: #17231f;
        --muted: #718078;
        --line: #e5ebe6;
        --accent: #197a5b;
        --accent-dark: #125d45;
        --canvas: #f5f8f5;
        --surface: #ffffff;
        --surface-soft: #fbfdfb;
        --surface-hover: #f2faf5;
        --input-line: #dce7df;
        --drop-line: #b6cbbd;
        --chip-bg: #f1f8f3;
        --chip-ink: #315b47;
        --chip-line: #deece2;
    }
    .stApp, [data-testid="stAppViewContainer"] {
        background: var(--canvas);
        color: var(--ink);
    }
    .main .block-container { color: var(--ink); }
    [data-testid="stMarkdownContainer"] p:not(.hero-copy),
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4 {
        color: var(--ink);
    }
    [data-testid="stCaptionContainer"] { color: var(--muted); }
    .main .block-container {
        max-width: 1120px;
        padding-top: 2.25rem;
        padding-bottom: 5rem;
    }
    [data-testid="stHeader"] { background: transparent; }
    section[data-testid="stSidebar"] {
        background: var(--surface);
        border-right: 1px solid var(--line);
    }
    section[data-testid="stSidebar"] > div { padding-top: 1.6rem; }
    section[data-testid="stSidebar"] h1 {
        color: var(--ink);
        letter-spacing: -0.04em;
    }
    .stButton > button {
        border-radius: 10px;
        border: 1px solid var(--line);
        background: var(--surface);
        color: var(--ink);
        font-weight: 600;
        min-height: 42px;
        transition: all .15s ease;
    }
    .stButton > button:hover {
        border-color: var(--accent);
        background: var(--surface-hover);
        color: var(--accent-dark);
    }
    .stButton > button[kind="primary"] {
        background: var(--accent);
        border-color: var(--accent);
        color: #fff;
    }
    .stButton > button[kind="primary"]:hover {
        background: var(--accent-dark);
        border-color: var(--accent-dark);
        color: #fff;
    }
    [data-testid="stChatMessage"] {
        background: transparent;
        padding: .55rem 0;
    }
    [data-testid="stChatMessageContent"] {
        border-radius: 15px;
    }
    [data-testid="stForm"] {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: .65rem .75rem;
        box-shadow: 0 8px 24px rgba(24, 56, 40, .07);
    }
    [data-testid="stTextInput"] input,
    [data-testid="stFileUploader"] section {
        background: var(--surface);
        color: var(--ink);
    }
    [data-testid="stForm"] [data-testid="stTextInput"] input {
        height: 46px;
        border-color: var(--input-line);
        border-radius: 11px;
        font-size: .98rem;
    }
    [data-testid="stForm"] [data-testid="stTextInput"] input::placeholder {
        color: var(--muted);
        opacity: 1;
    }
    [data-testid="stFileUploader"] {
        border-radius: 12px;
        border: 1px dashed var(--drop-line);
        background: var(--surface-soft);
        padding: .5rem;
    }
    [data-testid="stFileUploader"] button {
        border-radius: 9px;
        border: 1px solid var(--input-line);
        background: var(--surface);
        color: var(--ink);
        font-weight: 600;
    }
    [data-testid="stFileUploader"] button:hover {
        border-color: var(--accent);
        color: var(--accent-dark);
    }
    [data-testid="stMetric"] {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 14px 17px;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--surface);
        border-color: var(--line);
    }
    [data-testid="stExpander"] {
        background: var(--surface);
        border-color: var(--line);
    }
    .hero-card {
        background: linear-gradient(120deg, #123d30 0%, #197a5b 68%, #31916e 100%);
        border-radius: 22px;
        color: white;
        padding: 2.1rem 2.2rem;
        margin: .8rem 0 1.6rem;
        box-shadow: 0 16px 38px rgba(22, 91, 65, .16);
    }
    .hero-eyebrow {
        color: #bfe8d2;
        font-size: .78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .13em;
    }
    .hero-title {
        color: white;
        font-size: clamp(2rem, 4vw, 3.1rem);
        line-height: 1.1;
        letter-spacing: -.055em;
        font-weight: 750;
        margin: .45rem 0 .65rem;
    }
    .hero-copy {
        color: #e3f4e9 !important;
        font-size: 1.02rem;
        max-width: 650px;
        margin: 0;
    }
    .section-kicker {
        color: var(--accent);
        font-size: .75rem;
        font-weight: 750;
        text-transform: uppercase;
        letter-spacing: .12em;
        margin-bottom: -.25rem;
    }
    .source-chip {
        display: inline-block;
        background: var(--chip-bg);
        color: var(--chip-ink);
        border: 1px solid var(--chip-line);
        border-radius: 999px;
        padding: .3rem .65rem;
        margin: .15rem .2rem .1rem 0;
        font-size: .82rem;
    }
    .stAlert { border-radius: 12px; }
    #MainMenu, footer { visibility: hidden; }
    @media (max-width: 640px) {
        .main .block-container {
            padding: 1rem 1rem 5rem;
        }
        .hero-card {
            border-radius: 18px;
            padding: 1.45rem;
            margin: .35rem 0 1.15rem;
        }
        .hero-title {
            font-size: clamp(1.8rem, 8vw, 2.35rem);
            letter-spacing: -.045em;
        }
        .hero-copy {
            font-size: .95rem;
            line-height: 1.55;
        }
        [data-testid="stForm"] {
            border-radius: 13px;
            padding: .5rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

if st.session_state.dark_mode:
    st.markdown(
        """
        <style>
        :root {
            color-scheme: dark;
            --background-color: #111814;
            --secondary-background-color: #18221c;
            --text-color: #e7eee9;
            --primary-color: #72d2a4;
            --ink: #e7eee9;
            --muted: #a5b5ac;
            --line: #33433b;
            --accent: #72d2a4;
            --accent-dark: #9be2bc;
            --canvas: #111814;
            --surface: #18221c;
            --surface-soft: #1b2921;
            --surface-hover: #24372c;
            --input-line: #3b5145;
            --drop-line: #54705f;
            --chip-bg: #20382b;
            --chip-ink: #c3e8d1;
            --chip-line: #355543;
        }
        [data-testid="stChatInput"] {
            box-shadow: 0 8px 30px rgba(0, 0, 0, .24) !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "documents" not in st.session_state:
    st.session_state.documents = []

if "documents_error" not in st.session_state:
    st.session_state.documents_error = None

if "suggested_question" not in st.session_state:
    st.session_state.suggested_question = None

if "upload_widget_version" not in st.session_state:
    st.session_state.upload_widget_version = 0

if "upload_notice" not in st.session_state:
    st.session_state.upload_notice = None


# ============================================================
# API HELPERS
# ============================================================

def backend_health():
    try:
        response = requests.get(
            f"{API_URL}/health",
            timeout=8
        )

        if response.status_code == 200:
            return response.json()

        return None

    except (requests.RequestException, ValueError):
        return None


def get_documents():

    try:
        response = requests.get(
            f"{API_URL}/documents",
            timeout=30
        )

        if response.status_code == 200:

            data = response.json()

            if isinstance(data, list):
                st.session_state.documents_error = None
                return data

            if isinstance(data, dict):
                documents = data.get("documents")
                if isinstance(documents, list):
                    st.session_state.documents_error = None
                    return documents

                st.session_state.documents_error = (
                    "The backend returned an unexpected document list."
                )
                return None

        st.session_state.documents_error = (
            f"Document list request failed ({response.status_code})."
        )
        return None

    except requests.RequestException as error:
        st.session_state.documents_error = (
            f"Could not connect to the backend: {error}"
        )
        return None


def upload_document(uploaded_file):

    try:

        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                uploaded_file.type
            )
        }

        response = requests.post(
            f"{API_URL}/upload",
            files=files,
            timeout=300
        )

        return response

    except requests.RequestException as error:

        st.error(
            f"Could not connect to backend: {error}"
        )

        return None


def delete_document(filename):

    try:

        encoded_filename = quote(
            filename,
            safe=""
        )

        response = requests.delete(
            f"{API_URL}/documents/{encoded_filename}",
            timeout=30
        )

        return response

    except requests.RequestException:

        return None


def reindex_document(filename):

    try:

        encoded_filename = quote(
            filename,
            safe=""
        )

        response = requests.post(
            f"{API_URL}/documents/{encoded_filename}/reindex",
            timeout=60
        )

        return response

    except requests.RequestException:

        return None


def ask_backend(question, recent_questions=None):

    try:

        response = requests.post(
            f"{API_URL}/ask",
            json={
                "question": question,
                "recent_questions": recent_questions or [],
            },
            timeout=120
        )

        if response.status_code == 200:
            return response.json()

        try:
            error = response.json()

        except Exception:
            error = response.text

        return {
            "error": error,
            "status_code": response.status_code
        }

    except requests.RequestException as error:

        return {
            "error": str(error)
        }


def render_sources(sources):
    if not sources:
        return

    with st.expander(f"Sources and retrieved passages ({len(sources)})"):
        for source in sources:
            filename = source.get("source", "Unknown document")
            chunk_id = source.get("chunk_id", "Unknown")
            score = source.get("score")
            title = f"{filename} · Chunk {chunk_id}"
            if isinstance(score, (int, float)):
                title += f" · Relevance {score:.0%}"
            st.markdown(f"**{title}**")
            if source.get("text"):
                st.caption(source["text"])


def response_error(response):
    try:
        payload = response.json()
        if isinstance(payload, dict):
            return payload.get("detail", payload)
        return payload
    except ValueError:
        return response.text or f"Request failed ({response.status_code})."



# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # --------------------------------------------------------
    # BRAND
    # --------------------------------------------------------

    st.title("✦ Knowledge AI")

    st.caption(
        "Your private workspace for knowledge"
    )

    st.divider()

    # --------------------------------------------------------
    # NEW CHAT
    # --------------------------------------------------------

    if st.button(
        "＋  New chat",
        use_container_width=True
    ):

        st.session_state.messages = []

        st.rerun()

    # --------------------------------------------------------
    # NAVIGATION
    # --------------------------------------------------------

    st.caption("WORKSPACE")

    page = st.radio(
        "Navigation",
        [
            "Chat",
            "Documents"
        ],
        label_visibility="collapsed"
    )

    # --------------------------------------------------------
    # SYSTEM STATUS
    # --------------------------------------------------------

    st.caption("APPEARANCE")
    st.toggle(
        "Dark mode",
        key="dark_mode",
        help="Switch between the light and dark appearance."
    )

    st.caption("SYSTEM STATUS")

    health = backend_health()

    if health is None:

        st.warning(
            "Backend offline or unavailable",
            icon="⚠️"
        )

    elif not health.get("llm"):

        st.warning(
            "Backend connected · configure HF_TOKEN for AI",
            icon="⚠️"
        )

    else:

        st.success(
            "Backend and AI connected",
            icon="✅"
        )

    if health is not None and not health.get("vector_store"):
        st.caption("Upload a document to enable document answers.")

    st.divider()
    st.caption("UPLOADED DOCUMENTS")
    sidebar_documents = get_documents()
    if sidebar_documents is None:
        st.caption("Document list unavailable.")
    elif sidebar_documents:
        for document in sidebar_documents:
            name = (
                document.get("name", "Unknown document")
                if isinstance(document, dict)
                else str(document)
            )
            st.caption(f"📄 {name}")
    else:
        st.caption("No indexed documents yet.")

    st.divider()

    st.caption(
        "AI Knowledge Assistant"
    )

    st.caption(
        "Document-grounded RAG"
    )


# ============================================================
# CHAT PAGE
# ============================================================

if page == "Chat":

    # --------------------------------------------------------
    # PAGE HEADER
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-eyebrow">Your knowledge, in conversation</div>
            <div class="hero-title">Ask better questions.<br>Find clear answers.</div>
            <p class="hero-copy">Explore your uploaded reports and notes with answers grounded in your documents, with sources attached.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # WELCOME SCREEN
    # --------------------------------------------------------

    if not st.session_state.messages:

        st.write("")

        st.markdown('<div class="section-kicker">Get started</div>', unsafe_allow_html=True)
        st.subheader("What would you like to find?")
        st.caption("Ask a question about your documents, or add a document to build your knowledge base.")

        st.write("")

        # ----------------------------------------------------
        # CAPABILITIES
        # ----------------------------------------------------

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### 📚 Explore")

            st.caption(
                "Find key details across your uploaded files."
            )

        with col2:
            st.markdown("### 🎯 Get grounded answers")

            st.caption(
                "Answers include the document chunks they came from."
            )

        with col3:
            st.markdown("### ✨ Keep it simple")

            st.caption(
                "Ask naturally about topics, sections, or facts."
            )

        st.write("")

        prompt_cols = st.columns(3)
        suggested_prompts = [
            "Summarize my uploaded documents",
            "What are the key topics?",
            "Find important dates and numbers"
        ]
        for prompt_col, prompt in zip(prompt_cols, suggested_prompts):
            with prompt_col:
                if st.button(prompt, use_container_width=True):
                    st.session_state.suggested_question = prompt
                    st.rerun()

        # ----------------------------------------------------
        # WHAT CAN I DO?
        # ----------------------------------------------------

        with st.expander("What can I do?"):

            capability_col1, capability_col2 = (
                st.columns(2)
            )

            with capability_col1:

                st.markdown("### 📚 Documents")

                st.write(
                    """
                    • Ask questions about uploaded documents

                    • Summarize documents

                    • Find specific information

                    • Extract important facts

                    • Compare information
                    """
                )

            with capability_col2:

                st.markdown("### ⚡ Assistant")

                st.write(
                    """
                    • Answer from uploaded documents

                    • Show source passages

                    • Say when documents do not contain an answer
                    """
                )

    # --------------------------------------------------------
    # CHAT HISTORY
    # --------------------------------------------------------

    for message in st.session_state.messages:

        role = message["role"]

        with st.chat_message(role):

            st.markdown(
                message["content"]
            )

            render_sources(message.get("sources", []))

    # --------------------------------------------------------
    # CHAT COMPOSER
    # --------------------------------------------------------

    with st.form("chat_composer", clear_on_submit=True):
        input_col, send_col = st.columns([0.86, 0.14])
        with input_col:
            question = st.text_input(
                "Message",
                placeholder="Ask anything about your knowledge base...",
                label_visibility="collapsed"
            )
        with send_col:
            submitted = st.form_submit_button(
                "Send",
                type="primary",
                use_container_width=True
            )

    if not submitted:
        question = None

    question = question or st.session_state.pop(
        "suggested_question",
        None
    )

    # --------------------------------------------------------
    # ASK QUESTION
    # --------------------------------------------------------

    if question:

        question = question.strip()

        if not question:
            st.stop()

        recent_questions = [
            message["content"]
            for message in st.session_state.messages
            if message["role"] == "user"
        ][-8:]

        # ----------------------------------------------------
        # ----------------------------------------------------
        # USER MESSAGE
        # ----------------------------------------------------

        st.session_state.messages.append(
            {
                "role": "user",
                "content": question
            }
        )

        with st.chat_message("user"):

            st.markdown(question)

        # ----------------------------------------------------
        # ASSISTANT
        # ----------------------------------------------------

        with st.chat_message("assistant"):

            with st.spinner("Thinking..."):

                result = ask_backend(
                    question,
                    recent_questions,
                )

            # ------------------------------------------------
            # HANDLE RESULT
            # ------------------------------------------------

            if not result:

                answer = (
                    "I couldn't connect to the backend."
                )

                sources = []

            elif "error" in result:

                error_detail = result["error"]
                if isinstance(error_detail, dict):
                    answer = str(
                        error_detail.get(
                            "detail",
                            error_detail
                        )
                    )
                else:
                    answer = str(error_detail)

                sources = []

                st.error(
                    answer
                )

            else:

                answer = result.get(
                    "answer",
                    "No answer was returned."
                )

                sources = result.get(
                    "sources",
                    []
                )

            # ------------------------------------------------
            # ANSWER
            # ------------------------------------------------

            st.markdown(answer)
            render_sources(sources)

        # ----------------------------------------------------
        # SAVE ASSISTANT MESSAGE
        # ----------------------------------------------------

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
                "sources": sources
            }
        )

        st.rerun()


# ============================================================
# DOCUMENTS PAGE
# ============================================================

elif page == "Documents":

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    st.markdown('<div class="section-kicker">Your library</div>', unsafe_allow_html=True)
    st.title("Documents")

    st.caption(
        "Upload and manage the documents your assistant "
        "uses to answer questions."
    )

    st.write("")

    st.divider()

    # --------------------------------------------------------
    # DOCUMENT LIST
    # --------------------------------------------------------

    documents = get_documents()

    if documents is None:
        st.error(st.session_state.documents_error or "Could not load documents.")
        documents = []

    document_count = len(documents)

    if st.session_state.upload_notice:
        st.success(st.session_state.upload_notice)
        st.session_state.upload_notice = None

    upload_col, tip_col = st.columns([1.6, 1])

    with upload_col:
        with st.container(border=True):
            st.markdown('<div class="section-kicker">Add documents</div>', unsafe_allow_html=True)
            st.subheader("Build your knowledge base")
            st.caption("Choose a PDF, Word document, or plain-text file. We’ll extract and index its content for search.")

            uploaded_file = st.file_uploader(
                "Drop a file here or browse",
                type=["pdf", "docx", "txt"],
                key=f"document_upload_{st.session_state.upload_widget_version}",
                help="Supported formats: PDF, DOCX, TXT"
            )

            if uploaded_file:
                file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
                st.caption(f"Ready to add · {uploaded_file.name} · {file_size_mb:.2f} MB")

                if st.button(
                    "Upload and index document",
                    type="primary",
                    use_container_width=True,
                    key="upload_and_index"
                ):
                    with st.spinner("Uploading, extracting text, and building the search index..."):
                        response = upload_document(uploaded_file)

                    if response is None:
                        st.error("Upload failed. Check that the backend is running and try again.")
                    elif response.status_code in (200, 201):
                        try:
                            response_data = response.json()
                        except ValueError:
                            response_data = {}

                        chunks_added = response_data.get("chunks_added")
                        chunk_text = (
                            f" ({chunks_added} searchable chunks created)"
                            if isinstance(chunks_added, int)
                            else ""
                        )
                        st.session_state.upload_notice = (
                            f"{uploaded_file.name} was uploaded and indexed{chunk_text}."
                        )
                        st.session_state.upload_widget_version += 1
                        st.rerun()
                    elif response.status_code == 409:
                        st.warning("That file is already in your knowledge base.")
                    else:
                        st.error(f"Upload failed: {response_error(response)}")

    with tip_col:
        with st.container(border=True):
            st.markdown('<div class="section-kicker">How it works</div>', unsafe_allow_html=True)
            st.subheader("From file to answer")
            st.markdown(
                """
                1. **Choose** a PDF, DOCX, or TXT file.
                2. **Upload and index** it once.
                3. **Ask questions** in Chat and check the cited sources.
                """
            )
            st.caption("The document becomes available to search after indexing finishes.")

    st.write("")
    st.markdown('<div class="section-kicker">Your library</div>', unsafe_allow_html=True)
    st.subheader(f"Your files · {document_count}")

    if not documents and not st.session_state.documents_error:

        st.info(
            "Your knowledge base is empty. "
            "Upload a document to get started."
        )

    else:

        for index, document in enumerate(
            documents
        ):

            # ------------------------------------------------
            # API RESPONSE
            # ------------------------------------------------

            if isinstance(
                document,
                str
            ):

                filename = document

                chunks = None

            else:

                filename = document.get(
                    "filename",
                    document.get(
                        "name",
                        "Unknown document"
                    )
                )

                chunks = document.get(
                    "chunks"
                )

            # ------------------------------------------------
            # FILE TYPE
            # ------------------------------------------------

            extension = (
                filename.rsplit(".", 1)[-1].upper()
                if "." in filename
                else "FILE"
            )

            # ------------------------------------------------
            # DOCUMENT CARD
            # ------------------------------------------------

            with st.container(
                border=True
            ):

                left, middle, actions = st.columns(
                    [5, 2, 3]
                )

                # --------------------------------------------
                # INFORMATION
                # --------------------------------------------

                with left:

                    st.markdown(
                        f"### 📄 {filename}"
                    )

                    if chunks is not None:

                        st.caption(
                            f"{extension} · "
                            f"{chunks} chunks"
                        )

                    else:

                        size = document.get("size") if isinstance(document, dict) else None
                        size_label = (
                            f" · {size / (1024 * 1024):.1f} MB"
                            if isinstance(size, (int, float))
                            else ""
                        )
                        st.caption(f"{extension} document{size_label}")

                # --------------------------------------------
                # STATUS
                # --------------------------------------------

                with middle:

                    st.write("")

                    st.success(
                        "Indexed",
                        icon="✅"
                    )

                # --------------------------------------------
                # ACTIONS
                # --------------------------------------------

                with actions:

                    reindex_col, delete_col = (
                        st.columns(2)
                    )

                    # ----------------------------------------
                    # REINDEX
                    # ----------------------------------------

                    with reindex_col:

                        if st.button(
                            "Reindex",
                            key=(
                                f"reindex_"
                                f"{index}_"
                                f"{filename}"
                            ),
                            use_container_width=True
                        ):

                            with st.spinner(
                                "Reindexing..."
                            ):

                                response = (
                                    reindex_document(
                                        filename
                                    )
                                )

                            if (
                                response
                                and response.status_code == 200
                            ):

                                st.success(
                                    "Reindexed successfully.",
                                    icon="✅"
                                )

                                st.rerun()

                            else:

                                detail = (
                                    response_error(response)
                                    if response is not None
                                    else "Could not connect to the backend."
                                )
                                st.error(f"Reindex failed: {detail}", icon="❌")

                    # ----------------------------------------
                    # DELETE
                    # ----------------------------------------

                    with delete_col:

                        if st.button(
                            "Delete",
                            key=(
                                f"delete_"
                                f"{index}_"
                                f"{filename}"
                            ),
                            use_container_width=True
                        ):

                            response = (
                                delete_document(
                                    filename
                                )
                            )

                            if (
                                response
                                and response.status_code == 200
                            ):

                                st.success(
                                    "Document deleted.",
                                    icon="✅"
                                )

                                st.session_state.messages = []

                                st.rerun()

                            else:

                                detail = (
                                    response_error(response)
                                    if response is not None
                                    else "Could not connect to the backend."
                                )
                                st.error(f"Could not delete document: {detail}", icon="❌")

            st.write("")


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "AI Knowledge Assistant · RAG-powered · "
    "Built with FastAPI + Streamlit"
)