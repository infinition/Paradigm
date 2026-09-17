"""Grammar examples for the C4 extractor; none of these sentences is in the benchmark dataset."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmarks"))
from intent_temporal_fr import features, temporal_category  # noqa: E402


def test_future_markers():
    assert temporal_category("Tu enverras le rapport lundi.") == "FUTURE"
    assert temporal_category("Éteins la lumière dans vingt minutes.") == "FUTURE"
    assert temporal_category("Range le bureau plus tard.") == "FUTURE"
    assert temporal_category("Appelle-le quand tu auras terminé.") == "FUTURE"
    assert temporal_category("Ferme la porte, pas maintenant.") == "FUTURE"


def test_past_markers_and_tout_a_l_heure_resolution():
    assert temporal_category("Tu as envoyé le rapport ?") == "PAST_REFERENCE"
    assert temporal_category("T'avais rangé le bureau hier ?") == "PAST_REFERENCE"
    assert temporal_category("La lumière marchait avant ?") == "PAST_REFERENCE"
    assert temporal_category("Tu as fermé la porte tout à l'heure ?") == "PAST_REFERENCE"
    assert temporal_category("Ferme la porte tout à l'heure.") == "FUTURE"


def test_now_conditional_unspecified():
    assert temporal_category("Envoie le rapport maintenant.") == "NOW"
    assert temporal_category("Range le bureau vite fait.") == "NOW"
    assert temporal_category("Si tu peux, envoie le rapport.") == "CONDITIONAL"
    assert temporal_category("Envoie le rapport.") == "UNSPECIFIED"


def test_negation_and_actionability():
    assert features("N'envoie pas le rapport.")["negated"] is True
    assert features("Regarde pas le rapport.")["negated"] is True
    assert features("Surtout pas de rapport.")["negated"] is True
    assert features("Envoie le rapport sans le relire.")["negated"] is False
    assert features("Envoie le rapport.")["actionable_now"] is True
    assert features("Envoie le rapport demain.")["actionable_now"] is False
    assert features("Tu as envoyé le rapport ?")["actionable_now"] is False
    assert features("N'envoie pas le rapport.")["actionable_now"] is False
