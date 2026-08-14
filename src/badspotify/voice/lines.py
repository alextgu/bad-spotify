"""What the agent actually says out loud.

Two different jobs, and they are not the same line:

  the **quip**          the judge's one-liner. Personality, varies every time,
                        shown on the screens. "This is a funeral now."
  the **announcement**  what gets spoken. A fixed sentence with the song and
                        the moment slotted in: *"Now playing Bodies by Drowning
                        Pool, for your quiet library aisle."*

The announcement is deliberately the same shape every time, and it is
deliberately **sincere**. The agent believes it has read the room correctly and
made a good choice; it says so plainly, the way a DJ who is pleased with a
transition would. It never winks, never acknowledges a mismatch, and is never
smug -- as far as it is concerned, the song fits.

That is what makes it work. A varying joke delivered in a serious voice stops
landing by the third one, because the audience starts listening for the joke.
An announcement that earnestly claims the pick is *perfect* keeps working,
because the line names the music and the moment in one breath and asserts they
belong together -- leaving the audience to notice, every time, that they do
not.

Composition happens here rather than in the narrator so it can be tested
without an API key, and so the screens can show the exact string that was
spoken.
"""
from __future__ import annotations

import re

from ..schemas import SceneRead, Verdict

DEFAULT_TEMPLATE = "Now playing {title} by {artist} — the perfect fit for your {context}."

DEFAULT_GREETING = ("Hello. I'm your {name}. "
                    "I'll help you choose the perfect music for any moment.")
"""Said once, at startup. This is the only line the running product actually
speaks -- per-track narration is off by default (`voice.say` in config.yaml),
because a voice over every song is a latency problem and a ducking problem in
exchange for a joke the screens already tell.

{name} comes from `voice.agent_name`, and is the project's name. It is not
chosen yet, so the fallback is "DJ" and the greeting still works."""

DEFAULT_AGENT_NAME = "DJ"
"""Placeholders: {title} {artist} {context} {mood} {quip}. Set `voice.line`
in config.yaml to change it; set it empty to speak the raw quip instead."""

_LEADING_ARTICLE = re.compile(r"^(a|an|the)\s+", re.IGNORECASE)
_CONTEXT_MAX = 48


def context_phrase(scene: SceneRead | None) -> str:
    """The bit after "for your". Has to read as a noun phrase mid-sentence.

    Scene settings arrive in two shapes -- "quiet library aisle between tall
    shelves" from perception, and "a hospital waiting room at 3am" from someone
    typing into the box. "for your a hospital waiting room" is the kind of
    detail that makes a voice sound broken, so the article goes.
    """
    if scene is None:
        return "moment"

    text = (getattr(scene, "setting", "") or "").strip()
    if not text:
        mood = (getattr(scene, "mood_label", "") or "").strip()
        return f"{mood} moment" if mood else "moment"

    text = text.rstrip(" .!?,")
    text = _LEADING_ARTICLE.sub("", text)

    # Settings arrive as a list of clauses -- "sunlit public park, people
    # reading on the grass". The first clause is the place; the rest is detail
    # nobody needs spoken over a song intro. Always cut, not just when it's
    # long: the line has to be predictable to deliver, and a comma mid-sentence
    # makes the voice trail off.
    if "," in text:
        head = text.split(",", 1)[0].strip()
        if len(head) >= 3:
            text = head

    # Still too long: cut on a word boundary rather than mid-word.
    if len(text) > _CONTEXT_MAX:
        text = text[:_CONTEXT_MAX].rsplit(" ", 1)[0]

    # It sits mid-sentence, so it starts lowercase -- unless it's a proper
    # noun, which we detect crudely by the word not being all-lowercase
    # already in the source.
    if text[:1].isupper() and not text.split(" ")[0].isupper():
        text = text[0].lower() + text[1:]

    return text or "moment"


def greeting(name: str = "", template: str = DEFAULT_GREETING) -> str:
    """The startup line. Sincere, and the only thing the product says aloud.

    Never raises: an empty name falls back to "DJ", and a typo'd placeholder
    falls back to a plain greeting rather than starting the program in silence.
    """
    name = (name or "").strip() or DEFAULT_AGENT_NAME
    try:
        return (template or DEFAULT_GREETING).format(name=name).strip()
    except (KeyError, IndexError, ValueError):
        return DEFAULT_GREETING.format(name=name)


def announcement(
    verdict: Verdict,
    scene: SceneRead | None = None,
    template: str = DEFAULT_TEMPLATE,
    max_chars: int = 160,
) -> str:
    """Build the spoken line. Never raises, never returns empty.

    A missing template falls back to the quip; a broken template (someone put
    an unknown placeholder in config.yaml) falls back too, rather than taking
    the voice down. Silence is the only real bug.
    """
    quip = (getattr(verdict, "quip", "") or "").strip()
    if not template:
        return quip

    track = verdict.track
    fields = {
        "title": track.title,
        "artist": track.artist or "someone",
        "context": context_phrase(scene),
        "mood": (getattr(scene, "mood_label", "") or "this") if scene else "this",
        "quip": quip,
    }

    try:
        line = template.format(**fields).strip()
    except (KeyError, IndexError, ValueError):
        # An unknown placeholder is a config typo, not a reason to go quiet.
        return quip or f"Now playing {track.title}."

    if not line:
        return quip

    if len(line) > max_chars:
        line = line[:max_chars].rsplit(" ", 1)[0].rstrip(",;:") + "."
    return line
