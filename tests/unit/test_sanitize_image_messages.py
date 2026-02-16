"""Tests for sanitize_image_messages()."""

import copy

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from core.middleware.dynamic import sanitize_image_messages


def _img_block(url="https://example.com/img.png"):
    return {"type": "image_url", "image_url": {"url": url}}


def _text_block(text="hello"):
    return {"type": "text", "text": text}


class TestSanitizeImageMessages:
    def test_empty_messages(self):
        assert sanitize_image_messages([]) == []

    def test_none_messages(self):
        assert sanitize_image_messages(None) is None

    def test_text_only_passthrough(self):
        msgs = [
            HumanMessage(content="first"),
            AIMessage(content="reply"),
            HumanMessage(content="second"),
        ]
        result = sanitize_image_messages(msgs)
        assert len(result) == 3
        assert result[0].content == "first"
        assert result[1].content == "reply"
        assert result[2].content == "second"

    def test_historical_image_sanitized(self):
        msgs = [
            HumanMessage(content=[_text_block("describe this"), _img_block()]),
            AIMessage(content="It shows a cat"),
            HumanMessage(content="thanks"),
        ]
        result = sanitize_image_messages(msgs)
        # First HumanMessage (historical) should have image replaced
        assert len(result) == 3
        first_content = result[0].content
        assert isinstance(first_content, list)
        assert any(
            b.get("type") == "text" and "1 imagem(ns)" in b.get("text", "")
            for b in first_content
        )
        assert not any(b.get("type") == "image_url" for b in first_content)
        # Last HumanMessage preserved
        assert result[2].content == "thanks"

    def test_current_image_preserved(self):
        msgs = [
            HumanMessage(content="old message"),
            AIMessage(content="reply"),
            HumanMessage(content=[_text_block("new"), _img_block()]),
        ]
        result = sanitize_image_messages(msgs)
        last = result[2]
        assert isinstance(last.content, list)
        assert any(b.get("type") == "image_url" for b in last.content)

    def test_multiple_images_collapsed(self):
        msgs = [
            HumanMessage(content=[
                _text_block("look at these"),
                _img_block("img1.png"),
                _img_block("img2.png"),
                _img_block("img3.png"),
            ]),
            AIMessage(content="nice"),
            HumanMessage(content="next question"),
        ]
        result = sanitize_image_messages(msgs)
        first_content = result[0].content
        assert isinstance(first_content, list)
        # Should have text block + placeholder
        placeholder = [b for b in first_content if "3 imagem(ns)" in b.get("text", "")]
        assert len(placeholder) == 1
        assert not any(b.get("type") == "image_url" for b in first_content)

    def test_image_only_message(self):
        msgs = [
            HumanMessage(content=[_img_block()]),
            AIMessage(content="I see an image"),
            HumanMessage(content="what was it?"),
        ]
        result = sanitize_image_messages(msgs)
        first_content = result[0].content
        assert isinstance(first_content, list)
        assert len(first_content) == 1
        assert "1 imagem(ns)" in first_content[0]["text"]

    def test_mixed_content_preserved(self):
        msgs = [
            HumanMessage(content=[
                _text_block("before"),
                _img_block(),
                _text_block("after"),
            ]),
            HumanMessage(content="final"),
        ]
        result = sanitize_image_messages(msgs)
        first_content = result[0].content
        texts = [b["text"] for b in first_content if b.get("type") == "text"]
        assert "before" in texts
        assert "after" in texts
        assert any("1 imagem(ns)" in t for t in texts)
        assert not any(b.get("type") == "image_url" for b in first_content)

    def test_non_human_untouched(self):
        msgs = [
            SystemMessage(content="system"),
            AIMessage(content="ai reply"),
            ToolMessage(content="tool result", tool_call_id="tc1"),
            HumanMessage(content="user msg"),
        ]
        result = sanitize_image_messages(msgs)
        assert result[0].content == "system"
        assert result[1].content == "ai reply"
        assert result[2].content == "tool result"
        assert result[3].content == "user msg"

    def test_single_message_preserved(self):
        """Single HumanMessage is also the last one, so it should be preserved."""
        msgs = [
            HumanMessage(content=[_text_block("hi"), _img_block()]),
        ]
        result = sanitize_image_messages(msgs)
        assert len(result) == 1
        assert any(b.get("type") == "image_url" for b in result[0].content)

    def test_original_not_mutated(self):
        original_content = [_text_block("desc"), _img_block()]
        msg = HumanMessage(content=original_content, id="msg-1")
        msgs = [msg, HumanMessage(content="later")]

        original_copy = copy.deepcopy(msgs)
        sanitize_image_messages(msgs)

        # Original list unchanged
        assert len(msgs) == 2
        assert msgs[0] is msg
        # Original message content unchanged
        assert msgs[0].content == original_copy[0].content
        assert any(b.get("type") == "image_url" for b in msgs[0].content)

    def test_message_id_preserved(self):
        msgs = [
            HumanMessage(content=[_text_block("x"), _img_block()], id="msg-42"),
            HumanMessage(content="y", id="msg-43"),
        ]
        result = sanitize_image_messages(msgs)
        assert result[0].id == "msg-42"
        assert result[1].id == "msg-43"

    def test_string_content_human_message_untouched(self):
        """HumanMessages with string content (no list blocks) pass through."""
        msgs = [
            HumanMessage(content="plain text old"),
            HumanMessage(content="plain text new"),
        ]
        result = sanitize_image_messages(msgs)
        assert result[0].content == "plain text old"
        assert result[1].content == "plain text new"
