"""USSD state machine for MANYA.

The flow reads the SAME verified legal database the website uses, and its menus
are localized via the database-driven UI message table (UIMessage) and
verified ContentTranslation records.

Africa's Talking message framing:
    CON <menu>      -> session continues (user can input a number)
    END <farewell>  -> session terminates

Preserved per session: session id, phone number, language, current menu and
user selections. Errors are reported as generic friendly text only - no stack
traces ever reach the handset.
"""

import logging

from apps.languages.models import Language
from apps.languages.services.translation_service import TranslationService
from apps.legal.models import LegalCategory, LegalTopic
from apps.legal.services.content_query import get_verified_content
from apps.messaging.services.africastalking_sms import send_infosms
from apps.ussd.models import UssdSession
from apps.ussd.services.translation import content, ui

logger = logging.getLogger(__name__)


class UssdError(Exception):
    """A controlled USSD routing failure."""


class UssdService:
    """Resolve one USSD request into the next menu (state machine)."""

    def handle(self, payload):
        session_id = str(payload.get("sessionId") or "").strip()
        phone = str(payload.get("phoneNumber") or "").strip()
        text = str(payload.get("text") or "").strip()

        if "*" in text:
            text = text.split("*")[-1].strip()

        try:
            session = self._get_session(session_id, phone)
            response_text = self._route(session, text)
            try:
                session.save(
                    update_fields=["language_code", "menu", "data", "updated_at"]
                )
            except Exception:  # noqa: BLE001
                logger.exception("Could not persist USSD session state.")
            return {"response": response_text, "session": session}
        except Exception:  # noqa: BLE001
            logger.exception("USSD handler failed for session %s", session_id)
            return {"response": _generic_error(), "session": None}

    def _get_session(self, session_id, phone):
        if not session_id:
            raise UssdError("invalid-session")
        session, _ = UssdSession.objects.get_or_create(
            session_id=session_id,
            defaults={"phone_number": phone or "", "menu": "start"},
        )
        return session

    def _route(self, session, text):
        """Stateless menu resolution based on current state + user input."""
        if text == "":
            return self._menu_language(session, first=True)

        menu = session.menu or "start"

        if menu == "start":
            return self._handle_language_selection(session, text)
        if menu == "main":
            return self._handle_main_choice(session, text)
        if menu == "categories":
            return self._handle_categories(session, text)
        if menu == "issues":
            return self._handle_issues(session, text)
        if menu == "details":
            return self._handle_details(session, text)
        if menu == "referral_categories":
            return self._handle_referral_categories(session, text)
        if menu == "referrals":
            return self._handle_referrals(session, text)
        if menu == "referral_detail":
            return self._menu_main(session)
        if menu == "policy_list":
            return self._handle_policy_list(session, text)
        if menu == "choose_language":
            return self._handle_language_selection(session, text)

        return self._menu_language(session, first=True)

    # ------------------------------------------------------------------
    # Language selection
    def _handle_language_selection(self, session, text):
        languages = list(Language.active_public())
        try:
            idx = int(text) - 1
            if idx < 0 or idx >= len(languages):
                raise ValueError
        except ValueError:
            return self._error_retry(session, ui(session, "invalid_choice"))
        language = languages[idx]
        session.language_code = language.code
        session.menu = "main"
        session.data["user_selection"] = []
        session.data["view"] = ""
        return self._menu_main(session)

    def _menu_language(self, session, first=False):
        languages = list(Language.active_public())
        lines = [ui(session, "welcome"), ui(session, "tagline")]
        lines.append(ui(session, "change_language_prompt"))
        for i, language in enumerate(languages, start=1):
            lines.append(f"{i}. {language.native_name or language.name}")
        session.menu = "start" if first else "choose_language"
        return "CON " + "\n".join(lines)

    # ------------------------------------------------------------------
    # Main menu
    def _handle_main_choice(self, session, text):
        choice = text.strip()
        if choice == "1":
            session.menu = "categories"
            session.data["problem_flow"] = True
            return self._menu_categories(session)
        if choice == "2":
            return self._menu_awareness(session)
        if choice == "3":
            session.menu = "referral_categories"
            return self._menu_referral_categories(session)
        if choice == "4":
            session.menu = "policy_list"
            return self._menu_policy_list(session)
        if choice == "5":
            session.menu = "choose_language"
            return self._menu_language(session, first=False)
        if choice in ("0", "99"):
            return self._farewell(session)
        return self._error_retry(session, ui(session, "invalid_choice"))

    def _menu_main(self, session):
        lines = [ui(session, "welcome")]
        lines.append("1. " + ui(session, "i_have_a_problem"))
        lines.append("2. " + ui(session, "know_my_rights"))
        lines.append("3. " + ui(session, "find_legal_help"))
        lines.append("4. " + ui(session, "policy_updates"))
        lines.append("5. " + ui(session, "change_language"))
        session.menu = "main"
        return "CON " + "\n".join(lines)

    def _menu_awareness(self, session):
        """'Know my rights' - reads the same verified database."""
        legal_content = self._current_topic_content(session)
        if not legal_content:
            return "END " + ui(session, "no_verified_info")
        rights = content(session, legal_content, "rights_information")
        if not rights:
            return self._missing_section(session)
        lines = [ui(session, "understand_my_rights"), rights]
        session.menu = "details"
        session.data["view"] = "rights"
        return "CON " + "\n".join(lines)

    # ------------------------------------------------------------------
    # Categories -> issues -> topic options
    def _menu_categories(self, session):
        categories = list(
            LegalCategory.objects.filter(is_active=True).order_by(
                "display_order", "name"
            )
        )
        lines = [ui(session, "choose_issue")]
        for i, category in enumerate(categories, start=1):
            lines.append(f"{i}. {content(session, category, 'name')}")
        session.menu = "categories"
        return "CON " + "\n".join(lines)

    def _menu_issues(self, session, category):
        topics = list(
            LegalTopic.objects.filter(category=category, is_active=True).order_by(
                "display_order", "name"
            )
        )
        lines = [content(session, category, "name")]
        for i, topic in enumerate(topics, start=1):
            lines.append(f"{i}. {content(session, topic, 'name')}")
        session.menu = "issues"
        return "CON " + "\n".join(lines)

    def _menu_topic_options(self, session, topic):
        lines = [content(session, topic, "name")]
        lines.append("1. " + ui(session, "understand_my_rights"))
        lines.append("2. " + ui(session, "what_should_i_do"))
        lines.append("3. " + ui(session, "documents_i_need"))
        lines.append("4. " + ui(session, "find_legal_help"))
        lines.append("5. " + ui(session, "send_sms"))
        lines.append("6. " + ui(session, "listen"))
        lines.append("0. " + ui(session, "back"))
        session.menu = "details"
        return "CON " + "\n".join(lines)

    def _handle_categories(self, session, text):
        categories = list(
            LegalCategory.objects.filter(is_active=True).order_by(
                "display_order", "name"
            )
        )
        try:
            idx = int(text) - 1
            if idx < 0 or idx >= len(categories):
                raise ValueError
        except ValueError:
            return self._error_retry(session, ui(session, "invalid_choice"))
        category = categories[idx]
        session.data["user_selection"] = [category.slug]
        return self._menu_issues(session, category)

    def _handle_issues(self, session, text):
        category = self._selected_category(session)
        if category is None:
            return self._error_retry(session, ui(session, "invalid_choice"))
        topics = list(
            LegalTopic.objects.filter(category=category, is_active=True).order_by(
                "display_order", "name"
            )
        )
        try:
            idx = int(text) - 1
            if idx < 0 or idx >= len(topics):
                raise ValueError
        except ValueError:
            return self._error_retry(session, ui(session, "invalid_choice"))
        topic = topics[idx]
        session.data["user_selection"] = [category.slug, topic.slug]
        return self._menu_topic_options(session, topic)

    def _handle_details(self, session, text):
        topic = self._selected_topic(session)
        if topic is None:
            return self._error_retry(session, ui(session, "invalid_choice"))
        legal_content = get_verified_content(topic, session.language_code)
        if legal_content is None and session.language_code != "en":
            legal_content = get_verified_content(topic, "en")

        if text == "1":
            return self._show_rights(session, legal_content)
        if text == "2":
            return self._show_next_steps(session, legal_content)
        if text == "3":
            return self._show_documents(session, legal_content)
        if text == "4":
            return self._menu_referrals_for_topic(session, topic)
        if text == "5":
            return self._send_sms(session, legal_content)
        if text == "6":
            if getattr(session, "channel", "ussd") == "voice":
                # On a live phone call there is nothing to play for "Listen":
                # re-read the topic options instead of ending the call.
                return self._menu_topic_options(session, topic)
            return self._voice_prompt(session)
        if text in ("0", "00"):
            return self._menu_categories(session)
        return self._error_retry(session, ui(session, "invalid_choice"))

    def _show_rights(self, session, legal_content):
        if not legal_content:
            return self._missing_section(session)
        text = content(session, legal_content, "rights_information")
        if not text:
            return self._missing_section(session)
        session.menu = "details"
        return "CON " + "\n".join([ui(session, "understand_my_rights"), text])

    def _show_next_steps(self, session, legal_content):
        if not legal_content:
            return self._missing_section(session)
        text = content(session, legal_content, "next_steps")
        if not text:
            return self._missing_section(session)
        session.menu = "details"
        return "CON " + "\n".join([ui(session, "what_should_i_do"), text])

    def _show_documents(self, session, legal_content):
        if not legal_content:
            return self._missing_section(session)
        text = content(session, legal_content, "documents_required")
        if not text:
            return self._missing_section(session)
        session.menu = "details"
        return "CON " + "\n".join([ui(session, "documents_i_need"), text])

    def _missing_section(self, session):
        return "CON " + ui(session, "missing_translation_message")

    # ------------------------------------------------------------------
    # Referrals
    def _menu_referral_categories(self, session):
        from apps.referrals.models import Referral

        categories = list(
            Referral.objects.filter(is_verified=True)
            .exclude(category="")
            .values_list("category", flat=True)
            .distinct()
        )
        lines = [ui(session, "find_legal_help")]
        if not categories:
            return "END " + ui(session, "no_verified_info")
        for i, cat in enumerate(categories, start=1):
            lines.append(f"{i}. {self.t(cat, session)}")
        session.menu = "referral_categories"
        return "CON " + "\n".join(lines)

    def _handle_referral_categories(self, session, text):
        from apps.referrals.models import Referral

        categories = list(
            Referral.objects.filter(is_verified=True)
            .exclude(category="")
            .values_list("category", flat=True)
            .distinct()
        )
        try:
            idx = int(text) - 1
            if idx < 0 or idx >= len(categories):
                raise ValueError
        except ValueError:
            return self._error_retry(session, ui(session, "invalid_choice"))
        category = categories[idx]
        session.data["referral_category"] = category
        return self._menu_referrals_for_category(session, category)

    def _menu_referrals_for_category(self, session, category):
        from apps.referrals.models import Referral

        referrals = list(
            Referral.objects.filter(is_verified=True, category=category).order_by(
                "name"
            )
        )
        lines = [self.t(category, session)]
        for i, referral in enumerate(referrals, start=1):
            lines.append(f"{i}. {content(session, referral, 'name')}")
        session.menu = "referrals"
        return "CON " + "\n".join(lines)

    def _handle_referrals(self, session, text):
        from apps.referrals.models import Referral

        referral_list = session.data.get("referral_list")
        if referral_list:
            referrals = list(
                Referral.objects.filter(
                    is_verified=True, pk__in=referral_list
                ).order_by("name")
            )
        else:
            category = session.data.get("referral_category")
            referrals = list(
                Referral.objects.filter(is_verified=True, category=category).order_by(
                    "name"
                )
            )
        try:
            idx = int(text) - 1
            if idx < 0 or idx >= len(referrals):
                raise ValueError
        except ValueError:
            return self._error_retry(session, ui(session, "invalid_choice"))
        referral = referrals[idx]
        return self._menu_referral_detail(session, referral)

    def _menu_referral_detail(self, session, referral):
        lines = [content(session, referral, "name")]
        description = content(session, referral, "description")
        location = content(session, referral, "location")
        if description:
            lines.append(description)
        if location:
            lines.append(location)
        if referral.phone:
            lines.append(f"{ui(session, 'telephone')}: {referral.phone}")
        if referral.website:
            lines.append(referral.website)
        session.menu = "referral_detail"
        return "END " + "\n".join(lines)

    def _menu_referrals_for_topic(self, session, topic):
        """Find legal help for the selected topic (verified referrals only)."""
        from django.db.models import Q

        from apps.referrals.models import Referral

        referrals = list(
            Referral.objects.filter(is_verified=True)
            .filter(
                Q(category__icontains=topic.category.name)
                | Q(category__icontains=topic.name)
                | Q(services__icontains=topic.name)
            )
            .order_by("name")[:3]
        )
        if not referrals:
            return "CON " + ui(session, "no_verified_info")
        lines = [ui(session, "find_legal_help")]
        for i, ref in enumerate(referrals, start=1):
            lines.append(f"{i}. {content(session, ref, 'name')}")
        session.menu = "referrals"
        session.data["referral_list"] = [ref.pk for ref in referrals]
        return "CON " + "\n".join(lines)

    # ------------------------------------------------------------------
    # Policies
    def _menu_policy_list(self, session):
        from apps.policies.models import PolicyUpdate

        policies = list(PolicyUpdate.objects.filter(is_active=True)[:5])
        lines = [ui(session, "policy_updates")]
        if not policies:
            return "END " + ui(session, "no_verified_info")
        for i, policy in enumerate(policies, start=1):
            lines.append(f"{i}. {content(session, policy, 'title')}")
        session.menu = "policy_list"
        return "CON " + "\n".join(lines)

    def _handle_policy_list(self, session, text):
        from apps.policies.models import PolicyUpdate

        policies = list(PolicyUpdate.objects.filter(is_active=True)[:5])
        try:
            idx = int(text) - 1
            if idx < 0 or idx >= len(policies):
                raise ValueError
        except ValueError:
            return self._error_retry(session, ui(session, "invalid_choice"))
        policy = policies[idx]
        title = content(session, policy, "title")
        summary = content(session, policy, "summary")
        lines = [title]
        if summary:
            lines.append(summary)
        if policy.source:
            lines.append(content(session, policy, "source"))
        return "END " + "\n".join(lines)

    # ------------------------------------------------------------------
    # SMS + voice + navigation helpers
    def _send_sms(self, session, legal_content):
        if not session.phone_number:
            return "END " + ui(session, "sms_failed")
        try:
            send_infosms(
                session.phone_number,
                legal_content,
                message=self._translated_sms_message(session, legal_content),
            )
        except Exception:  # noqa: BLE001
            logger.warning("SMS failed from USSD", exc_info=True)
            return "END " + ui(session, "sms_failed")
        return "END " + ui(session, "sms_sent")

    def _voice_prompt(self, session):
        return "END " + ui(session, "voice_coming_soon")

    def _current_topic_content(self, session):
        topic = self._selected_topic(session)
        if topic is None:
            return None
        legal_content = get_verified_content(topic, session.language_code)
        if legal_content is None and session.language_code != "en":
            legal_content = get_verified_content(topic, "en")
        return legal_content

    def _selected_category(self, session):
        selection = session.data.get("user_selection") or []
        slug = selection[0] if selection else None
        if not slug:
            return None
        return LegalCategory.objects.filter(slug=slug, is_active=True).first()

    def _selected_topic(self, session):
        selection = session.data.get("user_selection") or []
        slug = selection[1] if len(selection) > 1 else None
        if not slug:
            return None
        return LegalTopic.objects.filter(slug=slug, is_active=True).first()

    def _error_retry(self, session, message):
        session.menu = session.menu or "main"
        return "CON " + message

    def _farewell(self, session):
        return "END " + ui(session, "exit")

    def t(self, text, session, content_type=None, content_id=None):
        """Translate a dynamic piece of text for the session language.

        Thin wrapper over the central translation service so no USSD code ever
        returns raw database strings. Results are cached, so Sunbird is only
        called once per missing string.
        """
        return TranslationService.translate(
            text,
            session.language_code,
            content_type=content_type,
            content_id=content_id,
        )

    def _translated_sms_message(self, session, legal_content):
        """Compose the confirmation SMS in the session language."""
        lines = [f"MANYA — {content(session, legal_content, 'title')}"]
        summary = content(session, legal_content, "summary")
        if summary:
            lines.append(summary.strip())
        steps = content(session, legal_content, "next_steps")
        if steps:
            lines.append(f"{ui(session, 'sms_next_step')}: {steps.strip()}")
        lines.append(ui(session, "sms_disclaimer"))
        return "\n".join(lines)

    # ------------------------------------------------------------------


def _generic_error():
    """Terminal safety net: user-facing text only, never internal details."""
    from apps.languages.services.translation_service import TranslationService

    language = Language.get_default()
    code = language.code if language else "en"
    return "END " + TranslationService.get_text("system_error", code)
