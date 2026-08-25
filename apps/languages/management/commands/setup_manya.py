import os

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.languages.models import ContentTranslation, Language, UIMessage
from apps.legal.models import (
    DISCLAIMER,
    LegalCategory,
    LegalContent,
    LegalSource,
    LegalTopic,
)
from apps.policies.models import PolicyUpdate
from apps.referrals.models import Referral

LANGUAGES = [
    {
        "code": "en",
        "name": "English",
        "native_name": "English",
        "is_active": True,
        "is_default": True,
        "display_order": 1,
    },
    {
        "code": "lg",
        "name": "Luganda",
        "native_name": "Luganda",
        "is_active": True,
        "is_default": False,
        "display_order": 2,
    },
    {
        "code": "teo",
        "name": "Ateso",
        "native_name": "Ateso",
        "is_active": True,
        "is_default": False,
        "display_order": 3,
    },
    {
        "code": "ach",
        "name": "Acholi",
        "native_name": "Acholi",
        "is_active": True,
        "is_default": False,
        "display_order": 4,
    },
]

UI_MESSAGES = {
    "en": {
        "welcome": "Welcome to MANYA",
        "tagline": "Know your rights. Know your next step.",
        "change_language_prompt": "Choose your language",
        "invalid_choice": "Invalid choice. Please try again.",
        "i_have_a_problem": "I have a problem",
        "know_my_rights": "Know my rights",
        "find_legal_help": "Find legal help",
        "policy_updates": "Policy Updates",
        "change_language": "Change Language",
        "understand_my_rights": "Understand my rights",
        "what_should_i_do": "What should I do?",
        "documents_i_need": "Documents I need",
        "send_sms": "Send SMS",
        "listen": "Listen",
        "back": "Back",
        "no_verified_info": "No verified information is available.",
        "missing_translation_message": (
            "This information is not available in your selected language."
        ),
        "sms_failed": "We could not send the SMS. Please try again later.",
        "sms_sent": "Information has been sent to your phone.",
        "exit": "Thank you for using MANYA. Goodbye.",
        "choose_issue": "Choose an issue",
        "telephone": "Tel",
        "voice_coming_soon": (
            "MANYA Voice is coming soon. Please use SMS or the website."
        ),
        "system_error": (
            "We are sorry - something went wrong. Please try again later."
        ),
    },
    "lg": {
        "welcome": "Tukwanirizza ku MANYA",
        "tagline": "Manya obuyinza bwo. Manya ky'olina okukola ekiddako.",
        "change_language_prompt": "Londa olulimi lwo",
        "invalid_choice": "Okulonda si kutuufu. Ddamu ogezeeko.",
        "i_have_a_problem": "Nina ekizibu",
        "know_my_rights": "Manya obuyinza bwo",
        "find_legal_help": "Funa obuyambi mu by'amateeka",
        "policy_updates": "Enkyukakyuka mu mateeka n'enkola",
        "change_language": "Kyusa olulimi",
        "understand_my_rights": "Tegeera obuyinza bwo",
        "what_should_i_do": "Nkole ki?",
        "documents_i_need": "Ebiwandiiko bye nneetaaga",
        "send_sms": "Sindika SMS",
        "listen": "Wuliriza",
        "back": "Ddayo",
        "no_verified_info": "Tewali mawulire makakasiddwa agaliwo.",
        "missing_translation_message": ("Amawulire gano tegali mu lulimi lw'olonze."),
        "sms_failed": ("Tetusobodde kusindika SMS. Ddamu ogezeeko oluvannyuma."),
        "sms_sent": "Amawulire gasindikiddwa ku ssimu yo.",
        "exit": "Webale okukozesa MANYA. Weeraba.",
        "choose_issue": "Londa ekizibu",
    },
    "teo": {
        "welcome": "MANYA arai aicikokin",
        "tagline": "Ngitela ebeonokin. Ngitela aite kere arai.",
        "change_language_prompt": "Kibo loke ajokoto",
        "invalid_choice": "Aiboisio ajokoto. Damu keba.",
        "i_have_a_problem": "Erai akwapit",
        "know_my_rights": "Ngitela ebeonokin",
        "find_legal_help": "Kibo aiboisio lo by legal",
        "policy_updates": "Erai ngitela",
        "change_language": "Kigora ajokoto",
        "understand_my_rights": "Ngitela ebeonokin",
        "what_should_i_do": "Arai kere akoni?",
        "documents_i_need": "Eiponei lo dokument",
        "send_sms": "Kisuba SMS",
        "listen": "Keworo",
        "back": "Damu",
        "no_verified_info": "Aiboisio akwapit aite.",
        "missing_translation_message": ("Eiponei akwapit aiboisio ajokoto."),
        "sms_failed": ("SMS aiboisio. Damu keba arai."),
        "sms_sent": "Akwapit kisuba ku ssimu.",
        "exit": "Webale MANYA. Damu keba.",
        "choose_issue": "Kibo akwapit",
    },
    "ach": {
        "welcome": "Wacok MANYA",
        "tagline": "Ngec kit ma twero. Ngec gin ma myero itim.",
        "change_language_prompt": "Yer leb ma imito",
        "invalid_choice": "Yero pe tye kakare. Tem doki.",
        "i_have_a_problem": "Atye ki peko",
        "know_my_rights": "Ngec twero na",
        "find_legal_help": "Nong kony me cik",
        "policy_updates": "Lok me cik",
        "change_language": "Lok leb",
        "understand_my_rights": "Ngec twero na",
        "what_should_i_do": "Ango ma myero atim?",
        "documents_i_need": "Papara ma amito",
        "send_sms": "Cwal SMS",
        "listen": "Winyo",
        "back": "Doki",
        "no_verified_info": "Pe tye ngec ma otyeko nongere.",
        "missing_translation_message": ("Ngec man pe tye i leb ma iyero."),
        "sms_failed": ("Pe onongo twero cwalo SMS. Tem doki lacen."),
        "sms_sent": "Ngec otyeko cwal i cim mamegi.",
        "exit": "Apwoyo me tic ki MANYA. Oriti.",
        "choose_issue": "Yer peko",
    },
}

LEGAL_SOURCES = [
    {
        "name": "Constitution of Uganda",
        "organization": "Parliament of Uganda",
        "source_type": "CONSTITUTION",
        "url": "https://ulii.org/ug/legis/const/1995",
        "document_title": "Constitution of the Republic of Uganda, 1995",
        "status": "ACTIVE",
        "authority_level": 1,
        "is_authoritative": True,
    },
    {
        "name": "Employment Act, 2006",
        "organization": "Parliament of Uganda",
        "source_type": "ACT",
        "url": "https://ulii.org/ug/legis/num_act/ea2006547",
        "document_title": "Employment Act, 2006",
        "status": "ACTIVE",
        "authority_level": 1,
        "is_authoritative": True,
    },
    {
        "name": "Land Act, 1998",
        "organization": "Parliament of Uganda",
        "source_type": "ACT",
        "url": "https://ulii.org/ug/legis/num_act/la199831",
        "document_title": "Land Act, 1998",
        "status": "ACTIVE",
        "authority_level": 1,
        "is_authoritative": True,
    },
]

LEGAL_CATEGORIES = [
    {"name": "Employment", "slug": "employment", "display_order": 1},
    {"name": "Land", "slug": "land", "display_order": 2},
    {"name": "Family", "slug": "family", "display_order": 3},
]

LEGAL_TOPICS = [
    {
        "name": "Unpaid salary / wages",
        "slug": "unpaid-salary",
        "category_slug": "employment",
        "display_order": 1,
        "content": {
            "en": {
                "title": "Unpaid salary / wages",
                "summary": "You are entitled to payment for work completed.",
                "rights_information": (
                    "Every worker has the right to be paid for work done. "
                    "If your employer has not paid you, you may have the right "
                    "to take further action."
                ),
                "what_this_means": (
                    "Your employer must pay you for the hours you worked. "
                    "This is a basic legal right."
                ),
                "next_steps": (
                    "1. Gather your employment records. "
                    "2. Ask your employer in writing. "
                    "3. Seek help from a verified legal-aid service if needed."
                ),
                "documents_required": (
                    "Employment contract, payslips, messages with employer, "
                    "time records."
                ),
                "legal_reference": "Employment Act, 2006; Constitution of Uganda Art 40(1)",
                "section_reference": "Employment Act, 2006, Sections 6-10",
                "verification_status": "VERIFIED",
            },
        },
    },
    {
        "name": "Wrongful termination",
        "slug": "wrongful-termination",
        "category_slug": "employment",
        "display_order": 2,
        "content": {
            "en": {
                "title": "Wrongful termination",
                "summary": "You may have rights if your employment was ended unfairly.",
                "rights_information": (
                    "Employment can only be terminated for a fair reason and "
                    "following a fair procedure. If you believe you were dismissed "
                    "unfairly, you may have the right to challenge the dismissal."
                ),
                "what_this_means": (
                    "Your employer must have a valid reason and follow proper "
                    "process before ending your employment."
                ),
                "next_steps": (
                    "1. Document the circumstances of your dismissal. "
                    "2. Seek advice from a legal professional. "
                    "3. File a complaint with the relevant labour office if appropriate."
                ),
                "documents_required": (
                    "Employment contract, termination letter, payslips, "
                    "witness statements."
                ),
                "legal_reference": "Employment Act, 2006",
                "section_reference": "Employment Act, 2006, Sections 30-35",
                "verification_status": "VERIFIED",
            },
        },
    },
    {
        "name": "Tenancy and eviction",
        "slug": "tenancy",
        "category_slug": "land",
        "display_order": 1,
        "content": {
            "en": {
                "title": "Tenancy and eviction",
                "summary": "Tenants and landlords have legal rights and responsibilities.",
                "rights_information": (
                    "A tenant has the right to quiet enjoyment of the premises. "
                    "A landlord must follow proper legal procedures before evicting "
                    "a tenant."
                ),
                "what_this_means": (
                    "You cannot be evicted without proper notice and due process. "
                    "Your landlord must obtain a court order."
                ),
                "next_steps": (
                    "1. Review your tenancy agreement. "
                    "2. Document any communications. "
                    "3. Seek legal advice before responding to eviction notices."
                ),
                "documents_required": (
                    "Tenancy agreement, rent receipts, eviction notice, "
                    "correspondence with landlord."
                ),
                "legal_reference": "Land Act, 1998",
                "section_reference": "Land Act, 1998, Sections 56-70",
                "verification_status": "VERIFIED",
            },
        },
    },
]

REFERRALS = [
    {
        "name": "Legal Aid Board",
        "description": "Government-funded legal aid for eligible Ugandans.",
        "category": "Government",
        "location": "Kampala",
        "phone": "+256414300600",
        "email": "info@legalaidboard.or.ug",
        "website": "https://www.legalaidboard.or.ug",
        "services": "Legal representation, advice, mediation",
        "is_verified": True,
        "last_verified": timezone.now().date(),
    },
    {
        "name": "Uganda Law Society Pro Bono",
        "description": "Free legal assistance for those who cannot afford a lawyer.",
        "category": "Professional",
        "location": "Kampala",
        "phone": "+256414346000",
        "email": "info@uls.or.ug",
        "website": "https://www.uls.or.ug",
        "services": "Legal advice, representation, referrals",
        "is_verified": True,
        "last_verified": timezone.now().date(),
    },
    {
        "name": "FIDA Uganda",
        "description": "Legal aid focused on women, children and families.",
        "category": "NGO",
        "location": "Kampala",
        "phone": "+256414286021",
        "email": "fidaug@fidauganda.or.ug",
        "website": "https://www.fidauganda.or.ug",
        "services": "Legal representation, counselling, advocacy",
        "is_verified": True,
        "last_verified": timezone.now().date(),
    },
]

POLICIES = [
    {
        "title": "Minimum Wage Policy Update 2024",
        "slug": "minimum-wage-policy-2024",
        "summary": "Updated guidelines on minimum wage compliance and enforcement.",
        "category": "Employment",
        "source": "Ministry of Gender, Labour and Social Development",
        "source_url": "https://www.mglsd.go.ug",
        "published_at": timezone.now().date(),
        "last_verified": timezone.now().date(),
        "is_active": True,
    },
    {
        "title": "Land Reform Guidelines 2024",
        "slug": "land-reform-guidelines-2024",
        "summary": "Guidelines on land registration, ownership verification and dispute resolution.",
        "category": "Land",
        "source": "Ministry of Lands, Housing and Urban Development",
        "source_url": "https://www.lands.go.ug",
        "published_at": timezone.now().date(),
        "last_verified": timezone.now().date(),
        "is_active": True,
    },
]


class Command(BaseCommand):
    help = "Bootstrap the complete MANYA production database."

    def handle(self, *args, **options):
        self._setup_superuser()
        self._setup_languages()
        self._setup_ui_messages()
        self._setup_legal_data()
        self._setup_referrals()
        self._setup_policies()
        self._setup_english_content_translations()

    def _setup_superuser(self):
        User = get_user_model()

        username = os.getenv("DJANGO_SUPERUSER_USERNAME")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

        if not username or not password:
            self.stdout.write(
                self.style.WARNING(
                    "DJANGO_SUPERUSER_USERNAME or DJANGO_SUPERUSER_PASSWORD "
                    "is not configured. Skipping admin creation."
                )
            )
            return

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email or "",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f"Superuser '{username}' created successfully.")
            )
            return

        changed = False

        if email and user.email != email:
            user.email = email
            changed = True

        if not user.is_staff:
            user.is_staff = True
            changed = True

        if not user.is_superuser:
            user.is_superuser = True
            changed = True

        if not user.is_active:
            user.is_active = True
            changed = True

        if changed:
            user.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Superuser '{username}' already exists and is configured."
            )
        )

    def _setup_languages(self):
        self.stdout.write("Setting up MANYA languages...")

        self.language_objects = {}

        for language_data in LANGUAGES:
            code = language_data["code"]

            language, created = Language.objects.update_or_create(
                code=code,
                defaults={
                    "name": language_data["name"],
                    "native_name": language_data["native_name"],
                    "is_active": language_data["is_active"],
                    "is_default": language_data["is_default"],
                    "display_order": language_data["display_order"],
                },
            )

            self.language_objects[code] = language

            action = "Created" if created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{action} language: {language.name} ({language.code})"
                )
            )

    def _setup_ui_messages(self):
        self.stdout.write("Setting up MANYA UI messages...")

        created_count = 0
        updated_count = 0

        for language_code, messages in UI_MESSAGES.items():
            language = self.language_objects[language_code]

            for key, text in messages.items():
                _, created = UIMessage.objects.update_or_create(
                    language=language,
                    key=key,
                    defaults={"text": text},
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"UI messages created: {created_count}"))
        self.stdout.write(self.style.SUCCESS(f"UI messages updated: {updated_count}"))

    def _setup_legal_data(self):
        self.stdout.write("Setting up MANYA legal data...")

        source_objects = {}

        for source_data in LEGAL_SOURCES:
            source, created = LegalSource.objects.update_or_create(
                name=source_data["name"],
                defaults={
                    "organization": source_data.get("organization", ""),
                    "source_type": source_data["source_type"],
                    "url": source_data.get("url", ""),
                    "document_title": source_data.get("document_title", ""),
                    "document_identifier": source_data.get("document_title", ""),
                    "status": source_data["status"],
                    "authority_level": source_data["authority_level"],
                    "is_authoritative": source_data["is_authoritative"],
                },
            )
            source_objects[source.name] = source
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} source: {source.name}"))

        category_objects = {}

        for category_data in LEGAL_CATEGORIES:
            category, created = LegalCategory.objects.update_or_create(
                slug=category_data["slug"],
                defaults={
                    "name": category_data["name"],
                    "is_active": True,
                    "display_order": category_data["display_order"],
                },
            )
            category_objects[category.slug] = category
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} category: {category.name}"))

        topic_objects = {}

        for topic_data in LEGAL_TOPICS:
            category = category_objects[topic_data["category_slug"]]
            topic, created = LegalTopic.objects.update_or_create(
                slug=topic_data["slug"],
                defaults={
                    "name": topic_data["name"],
                    "category": category,
                    "is_active": True,
                    "display_order": topic_data["display_order"],
                },
            )
            topic_objects[topic.slug] = topic
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} topic: {topic.name}"))

        content_created = 0
        content_updated = 0

        for topic_data in LEGAL_TOPICS:
            topic = topic_objects[topic_data["slug"]]
            for language_code, content_data in topic_data["content"].items():
                language = self.language_objects[language_code]
                source = source_objects.get("Employment Act, 2006")
                if topic_data["category_slug"] == "land":
                    source = source_objects.get("Land Act, 1998")
                elif topic_data["category_slug"] == "family":
                    source = source_objects.get("Constitution of Uganda")

                _, created = LegalContent.objects.update_or_create(
                    topic=topic,
                    language=language,
                    defaults={
                        "title": content_data["title"],
                        "summary": content_data.get("summary", ""),
                        "rights_information": content_data.get(
                            "rights_information", ""
                        ),
                        "what_this_means": content_data.get("what_this_means", ""),
                        "next_steps": content_data.get("next_steps", ""),
                        "documents_required": content_data.get(
                            "documents_required", ""
                        ),
                        "source_title": (
                            source.document_title or source.name if source else ""
                        ),
                        "source_url": source.url if source else "",
                        "legal_reference": content_data.get("legal_reference", ""),
                        "section_reference": content_data.get("section_reference", ""),
                        "verification_status": content_data.get(
                            "verification_status", "DRAFT"
                        ),
                        "disclaimer": DISCLAIMER,
                        "last_verified": (
                            timezone.now().date()
                            if content_data.get("verification_status") == "VERIFIED"
                            else None
                        ),
                    },
                )

                if created:
                    content_created += 1
                else:
                    content_updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"Legal content created: {content_created}")
        )
        self.stdout.write(
            self.style.SUCCESS(f"Legal content updated: {content_updated}")
        )

    def _setup_referrals(self):
        self.stdout.write("Setting up MANYA referrals...")

        created_count = 0
        updated_count = 0

        for referral_data in REFERRALS:
            referral, created = Referral.objects.update_or_create(
                name=referral_data["name"],
                defaults={
                    "description": referral_data.get("description", ""),
                    "category": referral_data.get("category", ""),
                    "location": referral_data.get("location", ""),
                    "phone": referral_data.get("phone", ""),
                    "email": referral_data.get("email", ""),
                    "website": referral_data.get("website", ""),
                    "services": referral_data.get("services", ""),
                    "is_verified": referral_data.get("is_verified", False),
                    "last_verified": referral_data.get("last_verified"),
                },
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"Referrals created: {created_count}"))
        self.stdout.write(self.style.SUCCESS(f"Referrals updated: {updated_count}"))

    def _setup_policies(self):
        self.stdout.write("Setting up MANYA policies...")

        created_count = 0
        updated_count = 0

        for policy_data in POLICIES:
            policy, created = PolicyUpdate.objects.update_or_create(
                slug=policy_data["slug"],
                defaults={
                    "title": policy_data["title"],
                    "summary": policy_data.get("summary", ""),
                    "category": policy_data.get("category", ""),
                    "source": policy_data.get("source", ""),
                    "source_url": policy_data.get("source_url", ""),
                    "published_at": policy_data.get("published_at"),
                    "last_verified": policy_data.get("last_verified"),
                    "is_active": policy_data.get("is_active", True),
                },
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"Policies created: {created_count}"))
        self.stdout.write(self.style.SUCCESS(f"Policies updated: {updated_count}"))

    def _setup_english_content_translations(self):
        self.stdout.write("Setting up English content translations...")

        english = Language.objects.filter(code="en", is_active=True).first()
        if not english:
            self.stdout.write(
                self.style.WARNING("English language not found. Skipping content translations.")
            )
            return

        created_count = 0
        updated_count = 0

        for category in LegalCategory.objects.filter(is_active=True):
            value = category.name or ""
            if not value:
                continue
            _, created = ContentTranslation.objects.update_or_create(
                language=english,
                content_type=ContentType.objects.get_for_model(LegalCategory),
                object_id=category.pk,
                field="name",
                defaults={"text": value, "is_verified": True, "translation_source": "system", "translation_status": "reviewed"},
            )
            created_count += 1 if created else 0
            updated_count += 0 if created else 1

        for topic in LegalTopic.objects.filter(is_active=True):
            value = topic.name or ""
            if not value:
                continue
            _, created = ContentTranslation.objects.update_or_create(
                language=english,
                content_type=ContentType.objects.get_for_model(LegalTopic),
                object_id=topic.pk,
                field="name",
                defaults={"text": value, "is_verified": True, "translation_source": "system", "translation_status": "reviewed"},
            )
            created_count += 1 if created else 0
            updated_count += 0 if created else 1

        for legal_content in LegalContent.objects.all():
            for field in (
                "rights_information",
                "next_steps",
                "documents_required",
                "summary",
                "title",
            ):
                value = getattr(legal_content, field, "") or ""
                if not value:
                    continue
                _, created = ContentTranslation.objects.update_or_create(
                    language=english,
                    content_type=ContentType.objects.get_for_model(LegalContent),
                    object_id=legal_content.pk,
                    field=field,
                    defaults={"text": value, "is_verified": True, "translation_source": "system", "translation_status": "reviewed"},
                )
                created_count += 1 if created else 0
                updated_count += 0 if created else 1

        for referral in Referral.objects.filter(is_verified=True):
            for field in ("name", "description", "location"):
                value = getattr(referral, field, "") or ""
                if not value:
                    continue
                _, created = ContentTranslation.objects.update_or_create(
                    language=english,
                    content_type=ContentType.objects.get_for_model(Referral),
                    object_id=referral.pk,
                    field=field,
                    defaults={"text": value, "is_verified": True, "translation_source": "system", "translation_status": "reviewed"},
                )
                created_count += 1 if created else 0
                updated_count += 0 if created else 1

        for policy in PolicyUpdate.objects.filter(is_active=True):
            for field in ("title", "summary"):
                value = getattr(policy, field, "") or ""
                if not value:
                    continue
                _, created = ContentTranslation.objects.update_or_create(
                    language=english,
                    content_type=ContentType.objects.get_for_model(PolicyUpdate),
                    object_id=policy.pk,
                    field=field,
                    defaults={"text": value, "is_verified": True, "translation_source": "system", "translation_status": "reviewed"},
                )
                created_count += 1 if created else 0
                updated_count += 0 if created else 1

        self.stdout.write(
            self.style.SUCCESS(f"Content translations created: {created_count}")
        )
        self.stdout.write(
            self.style.SUCCESS(f"Content translations updated: {updated_count}")
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("MANYA setup completed successfully.")
        )
