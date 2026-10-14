"""Word lists used by the sentiment, emotion and summary steps.

Valence values run from -3 (very negative) to +3 (very positive). The lists are
deliberately small and readable, so every score can be traced back to a word.
"""
from __future__ import annotations

from typing import Dict, FrozenSet

# (value, space-separated words). Later groups override earlier ones if a word repeats.
_VALENCE_GROUPS = (
    (1, "fine ok okay easy simple clear smooth useful support supported help helped helps agree agreed welcome ready stable steady fair calm comfortable interesting hope hopeful hopes promising solution solved solve resolved fixed effective efficient quick quickly fast convenient improve improved growth grew gain gains"),
    (2, "good great happy glad pleased satisfied helpful success successful win won best better benefit benefits improvement strong beautiful lovely nice enjoy enjoyed enjoyable impressive impressed proud grateful thank thanks thankful appreciate appreciated congratulations celebrate celebrated reliable trust trusted secure safe positive progress achieve achieved achievement opportunity reward rewarding exciting excited fun friendly kind generous valuable recommend recommended worth love loved"),
    (3, "excellent outstanding fantastic wonderful amazing perfect exceptional brilliant superb magnificent incredible phenomenal adore thrilled delighted"),
    (-1, "problem problems issue issues difficult hard trouble struggle struggling concern concerns doubt doubtful unclear confusing confused slow late delay delayed delays risk risks cost expensive costly lack lacking missing missed limited decline declined decrease drop dropped fall fell negative unfortunately complaint complaints sorry cancel cancelled canceled tired stress stressed stressful uncertain uncertainty tension conflict fault blame criticized loud setback cautious"),
    (-2, "bad poor angry sad unhappy disappointed disappointing frustrated frustrating annoying annoyed failure failed fail broken wrong error mistake useless worthless ignored rude unfair unacceptable weak painful harmful dangerous threat crisis suffer suffering loss lost damage damaged ruin ruined shame regret anxious afraid fear scared worry worried hostile cruel ugly boring stupid pathetic mess refuse refused denied reject rejected crashed crash"),
    (-3, "terrible horrible awful disgusting hate hatred horrific devastating catastrophic disaster tragic outrage outraged furious worst nightmare appalling dreadful abusive fraud scam"),
)

LEXICON: Dict[str, int] = {}
for _value, _words in _VALENCE_GROUPS:
    for _word in _words.split():
        LEXICON[_word] = _value

# A negation flips the next three scored words (see sentiment.py).
NEGATIONS: FrozenSet[str] = frozenset(
    "not no never neither nor without cannot dont didnt doesnt wasnt isnt arent "
    "werent wont wouldnt couldnt shouldnt havent hasnt hadnt cant".split()
)

# Intensifiers (>1) amplify the next scored word, softeners (<1) reduce it.
BOOSTERS: Dict[str, float] = {
    "very": 1.4, "extremely": 1.6, "really": 1.3, "completely": 1.5, "totally": 1.5,
    "absolutely": 1.6, "incredibly": 1.5, "highly": 1.3, "deeply": 1.4, "utterly": 1.6,
    "so": 1.2, "seriously": 1.3, "severely": 1.5,
    "slightly": 0.6, "somewhat": 0.6, "little": 0.7, "barely": 0.6, "mildly": 0.6,
}

_EMOTION_TEXT = {
    "joy": "happy happiness joy joyful delighted delight pleased glad enjoy enjoyed enjoying love loved lovely wonderful celebrate celebrated celebration fun excited exciting excitement cheerful smile smiled thrilled grateful amazing",
    "trust": "trust trusted reliable honest honesty loyal dependable confident confidence secure safe safety support supported faithful sincere respect respected commitment assure assured guarantee promise integrity stable",
    "anger": "angry anger furious outraged outrage mad hate hated rage annoyed annoying irritated irritating hostile resent resentment unfair rude insult insulted blame blamed threat threatened harass harassed frustrated frustrating frustration",
    "fear": "afraid fear fears scared frightened terrified worry worried worries anxious anxiety panic dread nervous risk risks danger dangerous threat uncertain uncertainty concern concerned alarm alarmed cautious",
    "sadness": "sad sadness unhappy depressed grief mourn mourning lonely loneliness hopeless regret regretted tears cry cried disappointed disappointing loss lost heartbroken sorrow gloomy",
}
EMOTION_WORDS: Dict[str, FrozenSet[str]] = {k: frozenset(v.split()) for k, v in _EMOTION_TEXT.items()}
EMOTION_LABELS: Dict[str, str] = {k: k.capitalize() for k in EMOTION_WORDS}

STOPWORDS: FrozenSet[str] = frozenset(
    "a about above after again against all also am an and any are as at be because been "
    "before being below between both but by can could did do does doing down during each "
    "few for from further had has have having he her here hers him his how i if in into is "
    "it its just me more most my no nor not of off on once only or other our out over own "
    "same she should so some such than that the their them then there these they this those "
    "through to too under until up very was we were what when where which while who why "
    "will with would you your yours said says say one two".split()
)
