"""Generate data/corpus.seed.json -- the hand-curated joke corpus.

Why hand-curated and not a 55k-track dataset? Because the joke only lands if
the judges RECOGNISE the song. Breadth is worthless here; recognisability is
everything. 40 well-chosen tracks that span the extremes of the vibe space
beat 55,000 tracks nobody can name.

Scale up later with:
  * MTG-Jamendo (55k tracks, 59 mood/theme tags, CC-licensed actual audio)
  * Deezer Mood Detection Dataset (valence/arousal, mapped to MSD ids)
  * every noise at once genre map (see scrape_everynoise.py)

Columns: valence, arousal, density, brightness, organicness  (all 0..1)
         recog = how likely a room full of students names it instantly
"""
import json
from pathlib import Path

#Each row stores track details, mood values, recognition, and tags
ROWS = [
    #Joyful songs
    ("sunshine", "Walking on Sunshine", "Katrina & The Waves", ["pop rock", "new wave"], .97, .80, .70, .92, .70, .95, ["upbeat", "sunny", "wedding"]),
    ("happy", "Happy", "Pharrell Williams", ["pop", "soul"], .96, .72, .60, .88, .65, .97, ["upbeat", "feelgood"]),
    ("dancingqueen", "Dancing Queen", "ABBA", ["europop", "disco"], .90, .68, .70, .85, .60, .96, ["disco", "celebration"]),
    ("september", "September", "Earth, Wind & Fire", ["funk", "disco"], .94, .75, .78, .86, .70, .93, ["celebration"]),
    ("allstar", "All Star", "Smash Mouth", ["pop rock"], .85, .70, .65, .80, .60, .94, ["meme", "2000s"]),

    #Novelty songs
    ("barbiegirl", "Barbie Girl", "Aqua", ["eurodance", "bubblegum"], .88, .78, .72, .95, .20, .92, ["novelty", "meme", "grating"]),
    ("babyshark", "Baby Shark", "Pinkfong", ["children's music"], .90, .82, .60, .97, .25, .95, ["novelty", "children", "grating", "infinite"]),
    ("rickroll", "Never Gonna Give You Up", "Rick Astley", ["pop", "blue-eyed soul"], .85, .62, .62, .78, .50, .98, ["meme", "bait"]),
    ("friday", "Friday", "Rebecca Black", ["teen pop"], .80, .60, .58, .90, .20, .82, ["novelty", "meme"]),
    ("sandstorm", "Sandstorm", "Darude", ["trance"], .60, .95, .88, .82, .05, .90, ["meme", "rave", "relentless"]),
    ("whatislove", "What Is Love", "Haddaway", ["eurodance"], .70, .80, .72, .80, .15, .88, ["meme", "90s"]),
    ("photograph", "Photograph", "Nickelback", ["post-grunge"], .45, .55, .68, .55, .55, .85, ["meme", "earnest"]),

    #Romance songs
    ("carelesswhisper", "Careless Whisper", "George Michael", ["sophisti-pop"], .35, .35, .55, .55, .70, .93, ["sax", "seduction", "awkward"]),
    ("letsgetiton", "Let's Get It On", "Marvin Gaye", ["soul"], .65, .40, .55, .55, .85, .88, ["seduction", "awkward"]),

    #Seasonal songs
    ("mariah", "All I Want for Christmas Is You", "Mariah Carey", ["christmas", "pop"], .93, .75, .80, .90, .60, .97, ["christmas", "seasonal", "wrong-season"]),
    ("lastchristmas", "Last Christmas", "Wham!", ["christmas", "synth-pop"], .70, .55, .65, .78, .45, .92, ["christmas", "seasonal", "wrong-season"]),

    #Funeral and dread songs
    ("funeralmarch", "Funeral March (Sonata No. 2)", "Frederic Chopin", ["classical", "romantic"], .05, .20, .45, .20, .95, .80, ["funeral", "death", "dread"]),
    ("ofortuna", "O Fortuna", "Carl Orff", ["classical", "choral"], .20, .95, .95, .60, .90, .89, ["apocalyptic", "epic", "doom"]),
    ("valkyries", "Ride of the Valkyries", "Richard Wagner", ["classical", "opera"], .40, .90, .92, .65, .92, .87, ["epic", "war", "overkill"]),
    ("mountainking", "In the Hall of the Mountain King", "Edvard Grieg", ["classical"], .30, .85, .70, .50, .90, .84, ["accelerating", "menace"]),
    ("adagio", "Adagio for Strings", "Samuel Barber", ["classical"], .08, .25, .50, .30, .95, .72, ["grief", "funeral"]),

    #Very heavy songs
    ("hammersmashed", "Hammer Smashed Face", "Cannibal Corpse", ["death metal"], .05, .97, .97, .45, .35, .55, ["death metal", "brutal", "growling"]),
    ("aghartha", "Aghartha", "Sunn O)))", ["drone metal"], .05, .30, .90, .10, .30, .30, ["drone", "oppressive", "endless"]),
    ("duality", "Duality", "Slipknot", ["nu metal"], .12, .93, .92, .50, .40, .80, ["rage", "screaming"]),
    ("funeraldoom", "Ete", "Bell Witch", ["funeral doom"], .04, .18, .78, .12, .45, .20, ["funeral doom", "glacial", "despair"]),
    ("cometodaddy", "Come to Daddy", "Aphex Twin", ["breakcore", "idm"], .08, .96, .90, .70, .05, .60, ["terrifying", "abrasive"]),
    ("merzbow", "Woodpecker No. 1", "Merzbow", ["harsh noise"], .05, .90, .99, .85, .05, .12, ["noise", "unlistenable", "punishment"]),
    ("gabber", "Thunderdome Anthem", "Various", ["gabber", "hardcore"], .30, .99, .95, .78, .05, .35, ["rave", "assault", "bpm"]),

    #Slow and sad songs
    ("hurt", "Hurt", "Johnny Cash", ["country", "americana"], .06, .18, .35, .28, .95, .86, ["regret", "death", "grief"]),
    ("madworld", "Mad World", "Gary Jules", ["indie pop"], .08, .15, .28, .25, .80, .84, ["bleak", "isolation"]),
    ("someonelikeyou", "Someone Like You", "Adele", ["pop", "soul"], .15, .30, .40, .45, .90, .93, ["heartbreak", "crying"]),
    ("creep", "Creep", "Radiohead", ["alternative rock"], .15, .45, .55, .40, .75, .91, ["self-loathing"]),
    ("disappear", "How to Disappear Completely", "Radiohead", ["art rock"], .07, .12, .40, .22, .70, .55, ["dissociation", "void"]),

    #Peaceful songs
    ("gymnopedie", "Gymnopedie No. 1", "Erik Satie", ["classical", "impressionism"], .55, .06, .18, .55, .98, .82, ["calm", "cafe", "gentle"]),
    ("clairdelune", "Clair de Lune", "Claude Debussy", ["classical", "impressionism"], .62, .08, .22, .60, .97, .85, ["calm", "moonlight"]),
    ("musicforairports", "1/1", "Brian Eno", ["ambient"], .55, .04, .15, .50, .35, .48, ["ambient", "weightless"]),
    ("weightless", "Weightless", "Marconi Union", ["ambient"], .50, .03, .18, .48, .30, .40, ["ambient", "anxiety-reducing"]),

    #High energy songs
    ("eyeofthetiger", "Eye of the Tiger", "Survivor", ["arena rock"], .70, .88, .80, .72, .55, .95, ["training", "montage"]),
    ("thunderstruck", "Thunderstruck", "AC/DC", ["hard rock"], .65, .92, .85, .80, .60, .92, ["adrenaline"]),
    ("xgonegiveit", "X Gon' Give It to Ya", "DMX", ["hip hop"], .40, .90, .82, .60, .45, .86, ["aggression", "entrance"]),

    #Jazz and unusual rhythm songs
    ("takefive", "Take Five", "Dave Brubeck", ["cool jazz"], .65, .40, .45, .60, .95, .80, ["5/4", "irregular", "cocktail"]),
    ("sowhat", "So What", "Miles Davis", ["modal jazz"], .55, .30, .38, .50, .95, .70, ["cool", "restrained"]),
    ("freejazz", "Free Jazz", "Ornette Coleman", ["free jazz"], .40, .85, .90, .75, .95, .30, ["atonal", "chaotic", "unlistenable"]),

    #Other useful songs
    ("africa", "Africa", "Toto", ["yacht rock", "soft rock"], .80, .55, .65, .75, .60, .94, ["meme", "earnest"]),
    ("achybreaky", "Achy Breaky Heart", "Billy Ray Cyrus", ["country"], .75, .65, .60, .80, .75, .78, ["line dance", "novelty"]),
    ("bodiesdrowning", "Bodies", "Drowning Pool", ["nu metal"], .10, .96, .90, .55, .40, .84, ["meme", "rage"]),
    ("yakety", "Yakety Sax", "Boots Randolph", ["novelty", "country"], .85, .88, .60, .90, .85, .80, ["benny hill", "chase", "undermining"]),
]

FIELDS = ["valence", "arousal", "density", "brightness", "organicness"]


def main() -> None:
    tracks = []
    for r in ROWS:
        tid, title, artist, genres, val, aro, den, bri, org, recog, tags = r
        tracks.append({
            "id": tid,
            "title": title,
            "artist": artist,
            "genres": genres,
            "vibe": dict(zip(FIELDS, [val, aro, den, bri, org])),
            "tags": tags,
            "recognisability": recog,
            "uri": None,
        })
    out = Path(__file__).resolve().parents[1] / "data" / "corpus.seed.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(tracks, indent=2))
    print(f"wrote {len(tracks)} tracks -> {out}")


if __name__ == "__main__":
    main()
