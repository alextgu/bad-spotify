"""What the agent says out loud.

The line is spoken over the start of a track, in a serious voice, to a room.
The failures that matter are the ones that make it sound broken -- "for your a
hospital waiting room", a sentence that runs past the song intro, or silence
because someone typo'd a placeholder in config.yaml.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from badspotify.perceive.scene import scene_from_text          # noqa: E402
from badspotify.schemas import Track, Verdict, Vibe            # noqa: E402
from badspotify.voice.lines import (                           # noqa: E402
    DEFAULT_TEMPLATE,
    announcement,
    context_phrase,
)


def verdict(title="Bodies", artist="Drowning Pool", quip="You looked comfortable."):
    return Verdict(track=Track(id="t", title=title, artist=artist, vibe=Vibe()),
                   strategy="genre_antipode", quip=quip)


# ------------------------------------------------------------- the context --


def test_leading_article_is_dropped():
    """"for your a hospital waiting room" is how a voice sounds broken."""
    scene = scene_from_text("a hospital waiting room at 3am")
    assert context_phrase(scene) == "hospital waiting room at 3am"


def test_long_setting_is_cut_at_the_first_clause():
    scene = scene_from_text("a sunlit public park, people reading on the grass")
    assert context_phrase(scene) == "sunlit public park"


def test_context_never_runs_past_the_song_intro():
    scene = scene_from_text("x" * 200)
    assert len(context_phrase(scene)) <= 48


def test_missing_scene_still_says_something():
    assert context_phrase(None) == "moment"


def test_a_scene_with_no_setting_falls_back_to_mood():
    scene = scene_from_text("a silent library during exam week")
    scene.setting = ""
    assert context_phrase(scene) == "hushed moment"


# -------------------------------------------------------- the announcement --


def test_the_default_line_names_the_song_and_the_moment():
    scene = scene_from_text("a silent library during exam week")
    line = announcement(verdict(), scene)

    assert line == ("Now playing Bodies by Drowning Pool, "
                    "for your silent library during exam week.")


def test_the_line_is_the_same_shape_every_time():
    """The format is straight; only the contents are absurd. That is the joke,
    and it stops working if the sentence itself keeps changing."""
    a = announcement(verdict("Sandstorm", "Darude"),
                     scene_from_text("a toddler's birthday party"))
    b = announcement(verdict("Hurt", "Johnny Cash"),
                     scene_from_text("an empty parking garage at night"))

    assert a.startswith("Now playing ") and b.startswith("Now playing ")
    assert a.endswith(".") and b.endswith(".")


def test_an_empty_template_speaks_the_quip_instead():
    line = announcement(verdict(), scene_from_text("a park"), template="")
    assert line == "You looked comfortable."


def test_a_typo_in_the_template_does_not_go_silent():
    """A bad placeholder in config.yaml is a typo, not a reason to lose the voice."""
    line = announcement(verdict(), scene_from_text("a park"),
                        template="Now playing {nonexistent}.")
    assert line == "You looked comfortable."


def test_a_typo_with_no_quip_still_says_the_song():
    line = announcement(verdict(quip=""), scene_from_text("a park"),
                        template="{nope}")
    assert "Bodies" in line


def test_a_long_line_is_trimmed_on_a_word_boundary():
    line = announcement(verdict("A" * 100, "B" * 100),
                        scene_from_text("a park"), max_chars=40)
    assert len(line) <= 41           # trim + the full stop
    assert line.endswith(".")
    assert "  " not in line


def test_custom_templates_work():
    scene = scene_from_text("a silent library during exam week")
    line = announcement(verdict(), scene,
                        template="{title}. For your {mood} {context}. Obviously.")
    assert line == ("Bodies. For your hushed silent library during exam week. "
                    "Obviously.")


def test_missing_artist_does_not_produce_a_dangling_by():
    line = announcement(verdict(artist=""), scene_from_text("a park"))
    assert "by someone" in line


@pytest.mark.parametrize("text", [
    "a sunlit park, people reading on the grass",
    "a hospital waiting room at 3am",
    "a toddler's birthday party, cake being cut",
    "a silent library during exam week",
    "an empty parking garage at night",
    "a first date at a candlelit restaurant",
])
def test_every_demo_scene_produces_a_speakable_line(text):
    """These six are the ones on stage. None may come out mangled."""
    line = announcement(verdict(), scene_from_text(text), DEFAULT_TEMPLATE)

    assert line.startswith("Now playing Bodies by Drowning Pool, for your ")
    assert line.endswith(".")
    # No dangling article straight after "for your" -- "for your a hospital
    # waiting room" is the failure this guards. Articles later in the phrase
    # ("at a candlelit restaurant") are fine and read naturally.
    after = line.split("for your ", 1)[1]
    assert not after.lower().startswith(("a ", "an ", "the "))
    assert len(line) < 120
