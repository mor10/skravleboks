import os
import json
import time
from typing import Iterable, List, Dict, Generator, Optional, Any
"""Thin wrapper around the official `ollama` Python package for chat + streaming.

Environment variables used:
  OLLAMA_HOST   - e.g. http://127.0.0.1:11434 (default provided by ollama lib if unset)
  OLLAMA_MODEL  - model name (default: smollm2:1.7b)
  OLLAMA_NUM_PREDICT - override number of tokens to predict
  OLLAMA_TOP_K  - override top_k sampling
  OLLAMA_TOP_P  - override top_p sampling
  OLLAMA_TEMPERATURE - default temperature if not passed explicitly

Design goals:
  * Keep a stable `prompt_stream(messages, **options)` generator API used by the CLI.
  * Leverage upstream streaming which yields structured chunks quickly.
  * Avoid per-chunk network overhead (handled internally by ollama lib / requests).
  * Provide a non-stream convenience method if needed later.
"""

from __future__ import annotations

import os
from typing import Iterable, Dict, Any, Generator, List

import ollama  # type: ignore


DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "smollm2:1.7b")


def _env_float(name: str) -> float | None:
    val = os.getenv(name)
    if val is None:
        return None
    try:
        return float(val)
    except ValueError:
        return None


def _env_int(name: str) -> int | None:
    val = os.getenv(name)
    if val is None:
        return None
    try:
        return int(val)
    except ValueError:
        return None


class OllamaClient:
    """Wrapper that normalizes streaming output to plain text chunks.

    Public method:
        prompt_stream(messages, **gen_options) -> yields text fragments
    """

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model

        # Preload default options from environment (optional overrides per call).
        self.default_options: Dict[str, Any] = {}
        if (v := _env_float("OLLAMA_TEMPERATURE")) is not None:
            self.default_options["temperature"] = v
        if (v := _env_int("OLLAMA_NUM_PREDICT")) is not None:
            self.default_options["num_predict"] = v
        if (v := _env_int("OLLAMA_TOP_K")) is not None:
            self.default_options["top_k"] = v
        if (v := _env_float("OLLAMA_TOP_P")) is not None:
            self.default_options["top_p"] = v

    def prompt_stream(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float | None = None,
        num_predict: int | None = None,
        top_k: int | None = None,
        top_p: float | None = None,
    ) -> Generator[str, None, None]:
        """Stream text chunks for given messages.

        Parameters mirror Ollama generation options (subset). Only options
        explicitly provided override environment defaults.
        """

        # Merge options precedence: call args > env defaults.
        options: Dict[str, Any] = dict(self.default_options)
        if temperature is not None:
            options["temperature"] = temperature
        if num_predict is not None:
            options["num_predict"] = num_predict
        if top_k is not None:
            options["top_k"] = top_k
        if top_p is not None:
            options["top_p"] = top_p

        # The ollama lib expects role names: system/user/assistant
        try:
            stream = ollama.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options=options if options else None,
            )
            for part in stream:
                # Each part is a dict; content nested in part['message']['content']
                try:
                    msg = part.get("message") or {}
                    content = msg.get("content")
                    if content:
                        yield content
                except Exception:
                    continue
        except Exception as e:  # Surface error as a single chunk so UI can show it
            yield f"[Ollama error] {e}"

    def prompt(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        """Non-stream convenience returning full text."""
        chunks = list(self.prompt_stream(messages, **kwargs))
        return "".join(chunks)


if __name__ == "__main__":  # Simple manual smoke test
    client = OllamaClient()
    msgs = [{"role": "user", "content": "Say hi in five words."}]
    print("Streaming response:")
    for c in client.prompt_stream(msgs, temperature=0.7):
        print(c, end="", flush=True)
    print()  # newline
            "model": overrides.get("model", self.model),
            "messages": messages,
            "options": self._build_options(**overrides),
        }

    # ------------- Public API -------------
    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float = 0.7,
        timeout: Optional[float] = None,
        **overrides,
    ) -> Generator[str, None, None]:
        """Stream response tokens/content pieces from Ollama.

        Yields only the textual content (may be sub-token fragments depending on server behavior).
        On error, yields a single error string beginning with 'Error:'.
        """
        url = f"{self.host}/api/chat"
        payload = self._chat_payload(messages, temperature=temperature, **overrides)
        timeout = timeout or OLLAMA_TIMEOUT

        try:
            with self._session.post(url, json=payload, timeout=timeout, stream=True) as resp:
                resp.raise_for_status()
                # iter_lines handles buffering; keep decode Unicode to avoid manual decoding per line.
                for raw_line in resp.iter_lines(decode_unicode=True):
                    if not raw_line:
                        continue
                    # Fast path: skip lines that obviously aren't JSON objects
                    if not raw_line.startswith("{"):
                        continue
                    try:
                        data = json.loads(raw_line)
                    except json.JSONDecodeError:
                        continue
                    # Ollama streams objects with a 'message' containing partial 'content'
                    msg = data.get("message") or {}
                    chunk = msg.get("content")
                    if chunk:
                        yield chunk
                    # Some implementations mark end with a 'done' flag; break early if present
                    if data.get("done"):
                        break
        except Exception as e:
            yield f"Error: {e}"

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float = 0.7,
        **overrides,
    ) -> str:
        """Convenience wrapper to return the full response as a single string."""
        return "".join(self.chat_stream(messages, temperature=temperature, **overrides))

    # Backwards compatibility alias (original method name)
    def prompt_stream(self, messages, temperature=0.7, **overrides):
        return self.chat_stream(messages, temperature=temperature, **overrides)


if __name__ == "__main__":  # Simple smoke test (will fail gracefully if server absent)
    client = OllamaClient()
    test_messages = [{"role": "user", "content": "Say hello in 5 words."}]
    print("Testing streaming response (may show error if server not running):")
    start = time.time()
    collected = []
    for piece in client.chat_stream(test_messages):
        print(piece, end="", flush=True)
        collected.append(piece)
    print("\n---\nElapsed: {:.2f}s, Length: {}".format(time.time() - start, len("".join(collected))))

