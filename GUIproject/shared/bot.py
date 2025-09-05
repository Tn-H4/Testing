import os, json, random, re
import numpy as np

try:
    import nltk
    from nltk.stem import WordNetLemmatizer
    from nltk.tokenize import word_tokenize
    NLTK_OK = True
except Exception:
    NLTK_OK = False
    WordNetLemmatizer = None
    word_tokenize = None

import torch
import torch.nn as nn
import torch.nn.functional as F

class ChatbotModel(nn.Module):
    def __init__(self, input_size, output_size):
        super().__init__()
        self.fc1 = nn.Linear(input_size, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, output_size)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.5)

    def forward(self, x):
        x = self.relu(self.fc1(x)); x = self.dropout(x)
        x = self.relu(self.fc2(x)); x = self.dropout(x)
        x = self.fc3(x)
        return x

# ---- A safe tokenizer that works even if NLTK data isn't downloaded ----
def safe_tokenize_and_lemmatize(text: str):
    text = text or ""
    tokens = []
    if NLTK_OK:
        try:
            # Try proper tokenization
            tokens = word_tokenize(text)
        except LookupError:
            # Fallback: basic split on non-letters
            tokens = re.findall(r"[A-Za-z']+", text)
        try:
            lem = WordNetLemmatizer()
            tokens = [lem.lemmatize(t.lower()) for t in tokens]
        except Exception:
            tokens = [t.lower() for t in tokens]
    else:
        tokens = [t.lower() for t in re.findall(r"[A-Za-z']+", text)]
    return tokens

class ChatbotAssistant:
    """
    Thin wrapper around your training/inference code for GUI use.
    Only inference is used here.
    """
    def __init__(self, intents_path, model_path, dimensions_path, function_mappings=None):
        self.model = None
        self.intents_path = intents_path
        self.model_path = model_path
        self.dimensions_path = dimensions_path

        self.documents = []
        self.vocabulary = []
        self.intents = []
        self.intents_responses = {}
        self.function_mappings = function_mappings or {}

        self.X = None
        self.y = None

        self._loaded_ok = False

        # Load everything on init
        self._parse_intents()
        self._load_model()

    # === Original helpers (adapted to use safe tokenizer) ===
    def _bag_of_words(self, words):
        return [1 if w in words else 0 for w in self.vocabulary]

    def _parse_intents(self):
        if not os.path.exists(self.intents_path):
            return
        with open(self.intents_path, "r", encoding="utf-8") as f:
            intents_data = json.load(f)
        for intent in intents_data.get("intents", []):
            tag = intent.get("tag")
            if not tag:
                continue
            if tag not in self.intents:
                self.intents.append(tag)
                self.intents_responses[tag] = intent.get("responses", [])
            for pattern in intent.get("patterns", []):
                p_words = safe_tokenize_and_lemmatize(pattern)
                self.vocabulary.extend(p_words)
                self.documents.append((p_words, tag))
        self.vocabulary = sorted(set(self.vocabulary))

    def _load_model(self):
        if not (os.path.exists(self.model_path) and os.path.exists(self.dimensions_path)):
            return
        with open(self.dimensions_path, "r", encoding="utf-8") as f:
            dims = json.load(f)
        input_size = dims["input_size"]
        output_size = dims["output_size"]
        self.model = ChatbotModel(input_size, output_size)
        # Support both torch>=2.0 (weights_only arg) and older
        try:
            state = torch.load(self.model_path, map_location="cpu", weights_only=True)
        except TypeError:
            state = torch.load(self.model_path, map_location="cpu")
        self.model.load_state_dict(state)
        self.model.eval()
        self._loaded_ok = True

    # === Public method used by ChatScreen ===
    def reply(self, user_text: str) -> str:
        """
        Returns a bot reply string. If the model or files are missing,
        returns a safe default string.
        """
        if not self._loaded_ok or not self.intents or not self.vocabulary:
            return "Sorry, my brain (model files) isn’t loaded yet."

        words = safe_tokenize_and_lemmatize(user_text)
        bow = self._bag_of_words(words)
        x = torch.tensor([bow], dtype=torch.float32)

        with torch.no_grad():
            logits = self.model(x)
            pred_idx = int(torch.argmax(logits, dim=1).item())
        intent = self.intents[pred_idx]

        # Optional: trigger mapped function
        fn = self.function_mappings.get(intent)
        if callable(fn):
            try:
                fn()  # you can adapt to return strings if you want to show output in chat
            except Exception:
                pass

        responses = self.intents_responses.get(intent, [])
        if responses:
            return random.choice(responses)
        return f"(No response configured for intent: {intent})"
