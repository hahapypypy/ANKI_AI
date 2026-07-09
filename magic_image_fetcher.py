import argparse
import base64
import datetime
import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Callable, Optional

addon_dir = os.path.abspath(os.path.dirname(__file__))
log_path = os.path.join(addon_dir, "debug.log")

DEFAULT_MODEL = "gemini-2.5-flash-image-preview"
ANKI_CONNECT_URL = "http://localhost:8765"
PICTURE_FIELD = "Picture"
REQUEST_TIMEOUT = 60
REQUEST_PAUSE_SECONDS = 0.3
FIXED_FIELDS = {
    "english": "英文",
    "chinese": "中文",
    "domain": "領域",
    "example": "例句",
    "root": "字根",
    "notes": "補充",
    "picture": PICTURE_FIELD,
}


def setup_logging():
    logger = logging.getLogger("ai_image_helper")
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)
    return logger


LOGGER = setup_logging()


def debug(msg):
    LOGGER.debug(msg)


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    debug(f"📂 Config path: {config_path}")
    try:
        with open(config_path, "r", encoding="utf-8") as handle:
            config = json.load(handle)
        debug("✅ Config loaded successfully")
        return config
    except FileNotFoundError:
        debug("❌ config.json not found. Please create it with your API keys.")
        return {}
    except Exception as exc:
        debug(f"❌ Error loading config.json: {exc}")
        return {}


CONFIG = load_config()


def check_ankiconnect_available():
    """Check if AnkiConnect is responding before starting."""
    debug("🔌 Checking AnkiConnect availability...")
    payload = {"action": "version", "version": 6}
    try:
        response = _post_json(ANKI_CONNECT_URL, payload, timeout=REQUEST_TIMEOUT)
        if response and response.get("result") is not None:
            debug(f"✅ AnkiConnect is available (version {response.get('result')})")
            return True
        debug("❌ AnkiConnect returned an unexpected response")
        return False
    except Exception as exc:
        debug(f"❌ Error checking AnkiConnect: {exc}")
        return False


def _post_json(url, payload, timeout=REQUEST_TIMEOUT):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8")
        return json.loads(body) if body else {}


def search_anki_for_empty_picture_notes(deck_name):
    debug(f"🔍 Searching for notes with empty {PICTURE_FIELD} field in deck '{deck_name}'")
    payload = {
        "action": "findNotes",
        "version": 6,
        "params": {
            "query": f'deck:"{deck_name}" {PICTURE_FIELD}:'
        },
    }
    try:
        response = _post_json(ANKI_CONNECT_URL, payload, timeout=REQUEST_TIMEOUT)
        result = response.get("result", [])
        debug(f"✅ Found {len(result)} notes with empty pictures")
        return result
    except urllib.error.URLError as exc:
        debug(f"❌ Connection error searching notes: {exc}")
        return []
    except Exception as exc:
        debug(f"❌ Error searching notes: {exc}")
        return []


def get_notes_info(note_ids):
    debug(f"📥 Fetching info for {len(note_ids)} notes")
    payload = {
        "action": "notesInfo",
        "version": 6,
        "params": {
            "notes": note_ids
        },
    }
    try:
        response = _post_json(ANKI_CONNECT_URL, payload, timeout=REQUEST_TIMEOUT)
        result = response.get("result", [])
        debug(f"✅ Retrieved info for {len(result)} notes")
        return result
    except urllib.error.URLError as exc:
        debug(f"❌ Connection error getting notes info: {exc}")
        return []
    except Exception as exc:
        debug(f"❌ Error getting notes info: {exc}")
        return []


def get_note_field_value(note_fields, field_name):
    field_info = note_fields.get(field_name, "")
    if isinstance(field_info, dict):
        return field_info.get("value", "") or ""
    return field_info or ""


def build_prompt(note_fields, extra_prompt=None):
    english = str(get_note_field_value(note_fields, FIXED_FIELDS["english"])).strip()
    chinese = str(get_note_field_value(note_fields, FIXED_FIELDS["chinese"])).strip()
    domain = str(get_note_field_value(note_fields, FIXED_FIELDS["domain"])).strip()
    example = str(get_note_field_value(note_fields, FIXED_FIELDS["example"])).strip()
    root = str(get_note_field_value(note_fields, FIXED_FIELDS["root"])).strip()
    notes = str(get_note_field_value(note_fields, FIXED_FIELDS["notes"])).strip()

    prompt_parts = [
        "Create a clean educational illustration for vocabulary learning.",
        "",
        "Word:",
        english,
        "",
        "Chinese Meaning:",
        chinese,
        "",
        "Domain:",
        domain,
        "",
        "Example Sentence:",
        example,
    ]

    if root:
        prompt_parts.extend(["", "Word Root:", root])

    if notes:
        prompt_parts.extend(["", "Additional Notes:", notes])

    prompt_parts.extend([
        "",
        "Requirements:",
        "",
        "Generate exactly ONE illustration.",
        "",
        "The illustration should visually explain the vocabulary.",
        "",
        "If the example sentence provides useful context,",
        "incorporate it naturally.",
        "",
        "Style:",
        "",
        "minimal",
        "",
        "educational",
        "",
        "clean",
        "",
        "easy to understand",
        "",
        "white background",
        "",
        "square",
        "",
        "no text",
        "",
        "no logo",
        "",
        "no watermark",
        "",
        "high semantic relevance",
    ])

    prompt_text = "\n".join(prompt_parts)
    if extra_prompt and str(extra_prompt).strip():
        return f"{str(extra_prompt).strip()}\n\n{prompt_text}"
    return prompt_text


def get_gemini_model():
    return CONFIG.get("GEMINI_MODEL", DEFAULT_MODEL)


def generate_image_with_gemini(prompt, model=None):
    api_key = CONFIG.get("GEMINI_API_KEY")
    if not api_key:
        debug("⚠️ Missing Gemini API key in config.json.")
        return None, "Missing Gemini API key"

    selected_model = model or get_gemini_model()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }

    start_time = time.time()
    debug(f"📡 Calling Gemini model: {selected_model}")
    try:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body) if body else {}
            elapsed = time.time() - start_time
            debug(f"⏱️ Gemini API elapsed: {elapsed:.2f}s")
            if data.get("error"):
                error_text = json.dumps(data.get("error"), ensure_ascii=False)
                debug(f"❌ Gemini API error: {error_text}")
                return None, error_text

            for candidate in data.get("candidates", []):
                for part in candidate.get("content", {}).get("parts", []):
                    inline_data = part.get("inlineData")
                    if inline_data and inline_data.get("data"):
                        image_bytes = base64.b64decode(inline_data["data"])
                        debug("✅ Gemini returned an image")
                        return image_bytes, None

            debug(f"⚠️ Gemini returned no image payload: {json.dumps(data, ensure_ascii=False)}")
            return None, json.dumps(data, ensure_ascii=False)
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        elapsed = time.time() - start_time
        debug(f"⏱️ Gemini API elapsed: {elapsed:.2f}s")
        debug(f"❌ Gemini API error response: {error_body}")
        return None, error_body
    except Exception as exc:
        elapsed = time.time() - start_time
        debug(f"⏱️ Gemini API elapsed: {elapsed:.2f}s")
        debug(f"❌ Gemini request failed: {exc}")
        return None, str(exc)


def build_media_filename(note_id):
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    return f"anki_vocab_{timestamp}_{note_id}.png"


def store_media_file(filename, image_bytes):
    payload = {
        "action": "storeMediaFile",
        "version": 6,
        "params": {
            "filename": filename,
            "data": base64.b64encode(image_bytes).decode("ascii"),
        },
    }
    try:
        response = _post_json(ANKI_CONNECT_URL, payload, timeout=REQUEST_TIMEOUT)
        if response.get("error"):
            debug(f"❌ Failed to store media file: {response.get('error')}")
            return False
        debug(f"📦 Stored media file: {filename}")
        return True
    except Exception as exc:
        debug(f"❌ Error storing media file: {exc}")
        return False


def update_note_picture(note_id, filename):
    debug(f"📝 Updating note {note_id} with file: {filename}")
    payload = {
        "action": "updateNoteFields",
        "version": 6,
        "params": {
            "note": {
                "id": note_id,
                "fields": {
                    PICTURE_FIELD: f'<img src="{filename}" style="max-width: 100%;">'
                },
            }
        },
    }
    try:
        response = _post_json(ANKI_CONNECT_URL, payload, timeout=REQUEST_TIMEOUT)
        if response.get("error"):
            debug(f"❌ Failed to update note {note_id}: {response.get('error')}")
            return False
        debug(f"✅ Successfully updated note {note_id}")
        return True
    except Exception as exc:
        debug(f"❌ Error updating note {note_id}: {exc}")
        return False


def process_notes(deck_name, extra_prompt=None, progress_callback=None, cancel_event=None):
    debug("🔄 Starting Gemini image generation process")

    if not CONFIG.get("GEMINI_API_KEY"):
        debug("❌ Missing Gemini API key. Aborting.")
        return {
            "total": 0,
            "processed": 0,
            "success": 0,
            "skipped": 0,
            "failed": 0,
            "cancelled": False,
            "elapsed_seconds": 0,
        }

    if not check_ankiconnect_available():
        debug("❌ AnkiConnect is not available. Make sure Anki is running and AnkiConnect add-on is installed.")
        return {
            "total": 0,
            "processed": 0,
            "success": 0,
            "skipped": 0,
            "failed": 0,
            "cancelled": False,
            "elapsed_seconds": 0,
        }

    start_time = time.time()
    note_ids = search_anki_for_empty_picture_notes(deck_name)
    notes = get_notes_info(note_ids)
    total = len(notes)

    processed_count = 0
    success_count = 0
    skipped_count = 0
    failed_count = 0

    if progress_callback:
        progress_callback(processed_count, total, "", success_count, skipped_count, failed_count)

    for note in notes:
        if cancel_event and cancel_event.is_set():
            debug("⚠️ Generation cancelled by user")
            break

        note_id = note.get("noteId")
        fields = note.get("fields", {})
        processed_count += 1

        picture_value = get_note_field_value(fields, FIXED_FIELDS["picture"]).strip()
        if picture_value:
            skipped_count += 1
            debug(f"⏭️ Skipping note {note_id}: Picture already exists")
            if progress_callback:
                progress_callback(processed_count, total, get_note_field_value(fields, FIXED_FIELDS["english"]) or "", success_count, skipped_count, failed_count)
            continue

        english = get_note_field_value(fields, FIXED_FIELDS["english"]).strip() or f"Note {note_id}"
        debug(f"📝 Processing note {processed_count}/{total} - ID: {note_id}")
        debug(f"📝 Note ID: {note_id}")
        debug(f"📝 English: {english}")

        prompt = build_prompt(fields, extra_prompt=extra_prompt)
        debug(f"📝 Final Prompt: {prompt}")

        image_bytes, error_message = generate_image_with_gemini(prompt)
        elapsed = time.time() - start_time
        if image_bytes:
            filename = build_media_filename(note_id)
            debug(f"🖼️ Image filename: {filename}")
            debug(f"⏱️ API elapsed: {elapsed:.2f}s")
            if store_media_file(filename, image_bytes) and update_note_picture(note_id, filename):
                success_count += 1
            else:
                failed_count += 1
        else:
            failed_count += 1
            debug(f"❌ Image generation failed for note {note_id}: {error_message}")

        if progress_callback:
            progress_callback(processed_count, total, english, success_count, skipped_count, failed_count)

        time.sleep(REQUEST_PAUSE_SECONDS)

    elapsed_seconds = int(time.time() - start_time)
    debug(f"🎉 Processing complete! Success={success_count}, Skipped={skipped_count}, Failed={failed_count}")
    return {
        "total": total,
        "processed": processed_count,
        "success": success_count,
        "skipped": skipped_count,
        "failed": failed_count,
        "cancelled": bool(cancel_event and cancel_event.is_set()),
        "elapsed_seconds": elapsed_seconds,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--deck", required=True)
    parser.add_argument("--extra-prompt", required=False, default="")
    args = parser.parse_args()

    debug("🔄 Starting AI 圖片生成助手 main()")
    debug(f"🎯 Settings: deck='{args.deck}', extra_prompt='{args.extra_prompt}'")
    process_notes(args.deck, extra_prompt=args.extra_prompt)


if __name__ == "__main__":
    main()
