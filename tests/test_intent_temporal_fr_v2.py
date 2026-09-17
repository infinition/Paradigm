"""Grammar examples for the C4b extractor; none of these sentences is in either benchmark dataset."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmarks"))
from intent_temporal_fr import temporal_category  # noqa: E402
from intent_temporal_fr_v2 import features_v2, temporal_category_v2  # noqa: E402


def test_subordinate_deferrals_are_future_whatever_the_tense_inside():
    assert temporal_category_v2("Envoie le rapport quand je te fais signe.") == "FUTURE"
    assert temporal_category_v2("Range le bureau une fois que tu as mangé.") == "FUTURE"
    assert temporal_category_v2("Lorsque la réunion sera finie, éteins la lumière.") == "FUTURE"
    assert temporal_category_v2("Dès que le fichier arrive, ouvre-le.") == "FUTURE"
    assert temporal_category_v2("Attends que je revienne avant d'envoyer le rapport.") == "FUTURE"
    assert temporal_category_v2("Attends avant de ranger le bureau.") == "FUTURE"
    assert temporal_category_v2("Après avoir relu le rapport, envoie-le.") == "FUTURE"


def test_past_main_clause_with_a_temporal_subordinate_is_a_past_reference():
    assert temporal_category_v2("Tu as envoyé le rapport quand je suis parti ?") == "PAST_REFERENCE"
    assert temporal_category_v2("T'avais rangé le bureau lorsque je t'ai appelé ?") == "PAST_REFERENCE"


def test_quand_as_a_question_is_not_a_deferral():
    assert temporal_category_v2("Quand est-ce que tu as envoyé le rapport ?") == "PAST_REFERENCE"
    assert temporal_category_v2("C'est quand, la réunion ?") == "UNSPECIFIED"


def test_indirect_question_si_is_not_conditional():
    assert temporal_category_v2("Regarde si la porte est fermée.") == "UNSPECIFIED"
    assert temporal_category_v2("Dis-moi si le rapport est parti.") == "UNSPECIFIED"
    assert temporal_category_v2("Vérifie juste si la lumière marche.") == "UNSPECIFIED"
    assert temporal_category_v2("Si tu peux, envoie le rapport.") == "CONDITIONAL"
    assert temporal_category_v2("Envoie le rapport, si jamais tu trouves le temps.") == "CONDITIONAL"


def test_version_1_behavior_is_kept_elsewhere():
    for s in ("Envoie le rapport demain.", "Tu as envoyé le rapport ?", "Envoie le rapport maintenant.", "Envoie le rapport."):
        assert temporal_category_v2(s) == temporal_category(s)
    assert features_v2("Envoie le rapport quand je te fais signe.")["actionable_now"] is False
    assert features_v2("N'envoie pas le rapport.")["negated"] is True
