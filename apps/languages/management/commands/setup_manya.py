from django.core.management.base import BaseCommand

from apps.languages.models import Language, UIMessage

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


class Command(BaseCommand):
    help = "Create/update MANYA languages and UI translations."

    def handle(self, *args, **options):
        self.stdout.write("Setting up MANYA languages...")

        language_objects = {}

        # ---------------------------------------------------------
        # Languages
        # ---------------------------------------------------------
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

            language_objects[code] = language

            action = "Created" if created else "Updated"

            self.stdout.write(
                self.style.SUCCESS(
                    f"{action} language: " f"{language.name} ({language.code})"
                )
            )

        # ---------------------------------------------------------
        # UI Messages
        # ---------------------------------------------------------
        self.stdout.write("Setting up MANYA UI messages...")

        created_count = 0
        updated_count = 0

        for language_code, messages in UI_MESSAGES.items():
            language = language_objects[language_code]

            for key, text in messages.items():
                _, created = UIMessage.objects.update_or_create(
                    language=language,
                    key=key,
                    defaults={
                        "text": text,
                    },
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"UI messages created: {created_count}"))

        self.stdout.write(self.style.SUCCESS(f"UI messages updated: {updated_count}"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("MANYA setup completed successfully."))
