"""Seed MANYA with demo data.

Usage:
    python manage.py seed_demo_data            # DRAFT-only demo data
    python manage.py seed_demo_data --verify   # ALSO mark the source-backed
                                               # English "Unpaid salary" record
                                               # VERIFIED so the full demo
                                               # journey can be shown.

INTEGRITY RULE:
MANYA never invents legal information. The seed only records laws that really
exist in Uganda and all legal *content* is saved as DRAFT unless --verify is
passed — and even then only a single conservative, source-backed English
record is verified. Other languages and topics stay DRAFT awaiting human
review / Sunbird translation in admin.

The verified "unpaid salary" record states the right to work under
satisfactory, fair and healthy conditions (Constitution of the Republic of
Uganda, 1995, Article 40(1)) plus general, pre-remedy next steps. It does not
invent sections of the Employment Act.
"""

from datetime import date

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.languages.models import Language, UIMessage
from apps.legal.models import (
    DISCLAIMER,
    LegalCategory,
    LegalContent,
    LegalSource,
    LegalTopic,
)
from apps.legal.services.source_service import SourceService

LANGUAGES = [
    {"code": "en", "name": "English", "native_name": "English", "default": True},
    {"code": "lg", "name": "Luganda", "native_name": "Luganda", "default": False},
    {"code": "teo", "name": "Ateso", "native_name": "Ateso", "default": False},
    {"code": "ach", "name": "Acholi", "native_name": "Acholi", "default": False},
]

# Sample, editable interface strings for local languages (UI text only — NOT
# legal content). Admins can refine these in Django admin at any time.
UI_SAMPLES = {
    "lg": {
        "change_language": "Kyusa olulimi",
        "i_have_a_problem": "Nnina ekizibu",
        "know_my_rights": "Amanya eddembe lyange",
        "find_legal_help": "Funa obuyambi bw'amateeka",
        "policy_updates": "Enkyusa z'amateeka",
        "change_language_prompt": "Londa olulimi",
        "understand_my_rights": "Amanya eddembe lyo",
        "what_should_i_do": "Nkooza ki?",
        "documents_i_need": "Ebiwandiiko byeetaagisa",
        "send_sms": "Tuma SMS",
        "listen": "Wulira",
        "exit": "Weebale nnyo mu MANYA.",
    },
    "teo": {
        "change_language": "Aíjaa ngoloiko",
        "welcome": "Apwoyo I MANYA",
        "i_have_a_problem": "Aiyonko eilimo",
        "know_my_rights": "Aao ajwa ur",
        "find_legal_help": "Igaaru ekitojai eilipi",
        "policy_updates": "Atojai kwa ameyaraan",
        "change_language_prompt": "Ipye ngoloiko",
        "understand_my_rights": "Ajwa ur ejo",
        "what_should_i_do": "Na aa nai?",
        "documents_i_need": "Mikano luadun",
        "send_sms": "SMS aipol",
        "listen": "Iwoo",
        "exit": "Apwoyo Ibeuny",
    },
    "ach": {
        "change_language": "Kwero kop le",
        "welcome": "Mito ber I MANYA",
        "i_have_a_problem": "An aya mone",
        "know_my_rights": "Waacko twol me twom",
        "find_legal_help": "Yenk ki decor loka",
        "policy_updates": "Loka motoo",
        "change_language_prompt": "Yer le",
        "understand_my_rights": "Niang twol me twom",
        "what_should_i_do": "An atim a itimona?",
        "documents_i_need": "Cic remo ma nito",
        "send_sms": "SMS aoro",
        "listen": "Winjo",
        "exit": "Apwoyo manok",
    },
}

CATEGORIES = [
    {
        "name": "Employment",
        "slug": "employment",
        "order": 1,
        "description": "Workplace issues: salary, dismissal, harassment, contracts.",
    },
    {
        "name": "Land",
        "slug": "land",
        "order": 2,
        "description": "Land rights, tenure, boundaries and landlord-tenant matters.",
    },
    {
        "name": "Family",
        "slug": "family",
        "order": 3,
        "description": "Marriage, divorce, children and family obligations.",
    },
    {
        "name": "Business",
        "slug": "business",
        "order": 4,
        "description": "Business registration, contracts and small enterprise issues.",
    },
    {
        "name": "Digital Rights",
        "slug": "digital-rights",
        "order": 5,
        "description": "Privacy, data, online safety and freedom of expression.",
    },
    {
        "name": "Education",
        "slug": "education",
        "order": 6,
        "description": "Access to education and learner entitlements.",
    },
    {
        "name": "Agriculture",
        "slug": "agriculture",
        "order": 7,
        "description": "Farmer rights, inputs and land for agricultural use.",
    },
]

TOPICS = {
    "employment": [
        ("Unpaid salary", "unpaid-salary", "Your employer has not paid your wages.", 1),
        ("Dismissal", "dismissal", "You have been removed from work.", 2),
        (
            "Workplace harassment",
            "workplace-harassment",
            "Harassment or abuse at work.",
            3,
        ),
        (
            "Contract problem",
            "contract-problem",
            "Issues with your employment contract.",
            4,
        ),
    ],
    "land": [("Land tenancy", "land-tenancy", "Landlord and tenant problems.", 1)],
    "family": [
        (
            "Marriage problems",
            "marriage-problems",
            "Divorce, custody or support issues.",
            1,
        )
    ],
    "business": [
        (
            "Small business problem",
            "small-business-problem",
            "Contracts and payment issues.",
            1,
        )
    ],
    "digital-rights": [
        ("Online privacy", "online-privacy", "Your data and privacy online.", 1)
    ],
    "education": [
        ("School access", "school-access", "Access to schooling questions.", 1)
    ],
    "agriculture": [
        ("Farming support", "farming-support", "Support for farms and farmers.", 1)
    ],
}

UNPAID_EN = {
    "title": "Unpaid salary / unpaid wages",
    "summary": (
        "Ugandan law protects workers' entitlement to wages. The Constitution "
        "of the Republic of Uganda (1995, as amended) guarantees every person "
        "the right to work under satisfactory, fair and healthy conditions "
        "(Article 40(1)). An employer who fails to pay agreed wages may be "
        "violating both the employment contract and the law. Available "
        "remedies can include recovery of the unpaid wages. This summary is "
        "general information, not legal advice."
    ),
    "what_this_means": (
        "In simple terms: you are entitled to be paid for the work you have "
        "done. If your employer withholds your salary it is a serious matter "
        "that the law addresses. Keep your contract and wage records, ask "
        "for payment in writing, and raise the issue promptly through proper "
        "channels."
    ),
    "rights_information": (
        "You have the right to work under satisfactory, fair and healthy "
        "conditions — Article 40(1) of the Constitution of the Republic of "
        "Uganda, 1995 (as amended). Refusal to pay wages you earned can be "
        "raised with your employer, the relevant labour authorities, or "
        "through the courts."
    ),
    "next_steps": (
        "1. Gather your documents: employment contract, payslips or wage "
        "records, and any communication about your salary. "
        "2. Ask your employer, in writing, to pay the unpaid wages. "
        "3. Contact the official labour administration (Ministry of Gender, "
        "Labour and Social Development) or a qualified labour officer. "
        "4. Consult a lawyer or a recognised legal-aid service for your "
        "specific situation."
    ),
    "documents_required": (
        "Employment contract, pay slips or wage records, bank records where "
        "relevant, and any letters, emails or messages about the unpaid "
        "salary."
    ),
    "legal_reference": "Constitution of the Republic of Uganda, 1995 (as amended), Article 40(1)",
    "section_reference": "Article 40(1)",
}


class Command(BaseCommand):
    help = "Seed MANYA with demo data (languages, categories, topics, DRAFT content)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--verify",
            action="store_true",
            help="Also mark the source-backed English 'Unpaid salary' record VERIFIED "
            "(for the live hackathon demo).",
        )

    def handle(self, *args, **options):
        self.verify = options["verify"]
        today = date.today()

        self.create_languages_and_ui()
        sources = self.create_sources()
        categories = self.create_categories()
        topics = self.create_topics(categories)
        self.create_content(topics, sources, today)
        self.create_referral_drafts()
        self.stdout.write(self.style.SUCCESS("Seed complete."))

    # ------------------------------------------------------------------ #
    def create_languages_and_ui(self):
        for index, lang in enumerate(LANGUAGES):
            Language.objects.get_or_create(
                code=lang["code"],
                defaults={
                    "name": lang["name"],
                    "native_name": lang["native_name"],
                    "is_active": True,
                    "is_default": lang["default"],
                    "display_order": index + 1,
                },
            )
        english = Language.objects.get(code="en")
        Language.objects.filter(is_default=True).exclude(code="en").update(
            is_default=False
        )
        english.is_default = True
        english.save()

        for code, messages in UI_SAMPLES.items():
            language = Language.objects.get(code=code)
            for key, text in messages.items():
                UIMessage.objects.get_or_create(
                    language=language, key=key, defaults={"text": text}
                )
        self.stdout.write("  Languages ready: en, lg, teo, ach.")

    def create_sources(self):
        constitution, _ = LegalSource.objects.get_or_create(
            name="Constitution of the Republic of Uganda, 1995",
            defaults={
                "organization": "Government of Uganda",
                "source_type": "CONSTITUTION",
                "url": "https://www.ilo.org/dyn/natlex/natlex4.detail?p_lang=en&p_isn=108607",
                "document_title": "Constitution of the Republic of Uganda, 1995 (as amended)",
                "jurisdiction": "UG",
                "status": "ACTIVE",
                "authority_level": 1,
                "is_authoritative": True,
            },
        )
        employment, _ = LegalSource.objects.get_or_create(
            name="Employment Act, 2006 (Uganda)",
            defaults={
                "organization": "Parliament of Uganda",
                "source_type": "ACT",
                "url": "https://ulii.org",
                "document_title": "The Employment Act, 2006",
                "jurisdiction": "UG",
                "status": "ACTIVE",
                "authority_level": 1,
                "is_authoritative": True,
            },
        )
        self.stdout.write(f"  Sources: {constitution.name} | {employment.name}")
        return {"constitution": constitution, "employment": employment}

    def create_categories(self):
        categories = {}
        for entry in CATEGORIES:
            obj, _ = LegalCategory.objects.get_or_create(
                slug=entry["slug"],
                defaults={
                    "name": entry["name"],
                    "display_order": entry["order"],
                    "description": entry["description"],
                    "is_active": True,
                },
            )
            categories[entry["slug"]] = obj
        return categories

    def create_content(self, topics, sources, today):
        english = Language.objects.get(code="en")
        other_languages = list(Language.active_public().exclude(code="en"))
        unpaid = topics["unpaid-salary"]

        # Shared source-attribution fields for the primary topic.
        base = {
            "source": sources["constitution"],
            "source_title": "Constitution of the Republic of Uganda, 1995 (as amended)",
            "source_url": sources["constitution"].url,
            "legal_reference": UNPAID_EN["legal_reference"],
            "section_reference": UNPAID_EN["section_reference"],
            "disclaimer": DISCLAIMER,
            "verification_status": "DRAFT",
            "last_verified": None,
        }

        # English: full source-backed content, DRAFT unless --verify.
        en_content, created = LegalContent.objects.get_or_create(
            topic=unpaid,
            language=english,
            defaults={
                **base,
                "title": UNPAID_EN["title"],
                "summary": UNPAID_EN["summary"],
                "what_this_means": UNPAID_EN["what_this_means"],
                "rights_information": UNPAID_EN["rights_information"],
                "next_steps": UNPAID_EN["next_steps"],
                "documents_required": UNPAID_EN["documents_required"],
            },
        )
        if not created:
            for field, value in {
                "summary": UNPAID_EN["summary"],
                "what_this_means": UNPAID_EN["what_this_means"],
                "rights_information": UNPAID_EN["rights_information"],
                "next_steps": UNPAID_EN["next_steps"],
                "documents_required": UNPAID_EN["documents_required"],
                "legal_reference": UNPAID_EN["legal_reference"],
                "section_reference": UNPAID_EN["section_reference"],
            }.items():
                setattr(en_content, field, value)
            en_content.source = sources["constitution"]
            en_content.save()

        # Other languages: DRAFT placeholder records so the UI can correctly
        # show "not yet available in your selected language" until a human
        # translates + verifies (Sunbird workflow in admin).
        for language in other_languages:
            LegalContent.objects.get_or_create(
                topic=unpaid,
                language=language,
                defaults={
                    **base,
                    "title": f"{UNPAID_EN['title']} ({language.native_name})",
                    "verification_status": "DRAFT",
                },
            )

        if self.verify and not en_content.is_public:
            en_content.verification_status = "VERIFIED"
            en_content.last_verified = today
            en_content.save()
            if en_content.source:
                SourceService.mark_verified(
                    en_content.source, verified_at=timezone.now()
                )
            self.stdout.write(
                self.style.SUCCESS(
                    "  VERIFIED: 'Unpaid salary' (en) — source-backed, ready for demo."
                )
            )

    def create_referral_drafts(self):
        # INTEGRITY: never publish unverified referrals. Seed only placeholders
        # which are invisible publicly until an admin verifies them.
        from apps.referrals.models import Referral

        Referral.objects.get_or_create(
            name="Ministry of Gender, Labour and Social Development — Labour Dept",
            defaults={
                "description": (
                    "Official government labour ministry. Contact details to be "
                    "confirmed by an administrator before this becomes public."
                ),
                "category": "Employment",
                "website": "https://www.mglsd.go.ug",
                "is_verified": False,
            },
        )
        self.stdout.write(
            "  Referrals: placeholders added (not public until an admin verifies)."
        )

    def create_topics(self, categories):
        topics = {}
        for cat_slug, entries in TOPICS.items():
            for name, slug, description, order in entries:
                obj, _ = LegalTopic.objects.get_or_create(
                    slug=slug,
                    defaults={
                        "name": name,
                        "category": categories[cat_slug],
                        "description": description,
                        "display_order": order,
                        "is_active": True,
                    },
                )
                topics[slug] = obj
        return topics
