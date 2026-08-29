"""Family legal seed data for setup_manya.

English copy is general information drawn from named Ugandan statutes.
It does not invent section numbers. Machine-quality Luganda, Ateso and
Acholi strings are stored as reviewed ContentTranslation rows so USSD/SMS
are fully translated without a hardcoded language switch. Administrators
should still review those translations.
"""

FAMILY_SOURCES = [
    {
        "name": "Marriage Act",
        "organization": "Parliament of Uganda",
        "source_type": "ACT",
        "url": "https://ulii.org/akn/ug/act/ord/1904/14",
        "document_title": "Marriage Act",
        "status": "ACTIVE",
        "authority_level": 1,
        "is_authoritative": True,
    },
    {
        "name": "Customary Marriage (Registration) Act",
        "organization": "Parliament of Uganda",
        "source_type": "ACT",
        "url": "https://ulii.org/akn/ug/act/1973/16",
        "document_title": "Customary Marriage (Registration) Act",
        "status": "ACTIVE",
        "authority_level": 1,
        "is_authoritative": True,
    },
    {
        "name": "Divorce Act",
        "organization": "Parliament of Uganda",
        "source_type": "ACT",
        "url": "https://ulii.org/akn/ug/act/ord/1904/15",
        "document_title": "Divorce Act",
        "status": "ACTIVE",
        "authority_level": 1,
        "is_authoritative": True,
    },
    {
        "name": "Children Act",
        "organization": "Parliament of Uganda",
        "source_type": "ACT",
        "url": "https://ulii.org/akn/ug/act/1996/6",
        "document_title": "Children Act (as amended)",
        "status": "ACTIVE",
        "authority_level": 1,
        "is_authoritative": True,
    },
    {
        "name": "Domestic Violence Act, 2010",
        "organization": "Parliament of Uganda",
        "source_type": "ACT",
        "url": "https://ulii.org/akn/ug/act/2010/3",
        "document_title": "Domestic Violence Act, 2010",
        "status": "ACTIVE",
        "authority_level": 1,
        "is_authoritative": True,
    },
    {
        "name": "Succession Act",
        "organization": "Parliament of Uganda",
        "source_type": "ACT",
        "url": "https://ulii.org/akn/ug/act/ord/1906/1",
        "document_title": "Succession Act (as amended, including 2022)",
        "status": "ACTIVE",
        "authority_level": 1,
        "is_authoritative": True,
    },
    {
        "name": "Administrator-General's Act",
        "organization": "Parliament of Uganda",
        "source_type": "ACT",
        "url": "https://ulii.org/akn/ug/act/1933/8",
        "document_title": "Administrator-General's Act",
        "status": "ACTIVE",
        "authority_level": 1,
        "is_authoritative": True,
    },
]


def _en(
    summary,
    rights,
    means,
    next_steps,
    docs,
    legal_reference,
    section_reference="",
    title=None,
):
    payload = {
        "summary": summary,
        "rights_information": rights,
        "what_this_means": means,
        "next_steps": next_steps,
        "documents_required": docs,
        "legal_reference": legal_reference,
        "section_reference": section_reference,
        "verification_status": "VERIFIED",
    }
    if title:
        payload["title"] = title
    return payload


def _topic(order, slug, name, source_name, content_en, description=""):
    content_en = dict(content_en)
    content_en.setdefault("title", name)
    return {
        "name": name,
        "slug": slug,
        "category_slug": "family",
        "display_order": order,
        "description": description,
        "source_name": source_name,
        "content": {"en": content_en},
    }


HELP = (
    "1. Write down what happened and gather any documents. "
    "2. Contact a probation and social welfare officer, police Family and "
    "Child Protection unit, or a verified legal-aid service such as FIDA. "
    "3. Ask a qualified legal professional about your specific situation."
)

CONST = "Constitution of the Republic of Uganda, 1995"
CHILDREN = "Children Act (as amended)"
DVA = "Domestic Violence Act, 2010"
MARRIAGE = "Marriage Act"
CUSTOMARY = "Customary Marriage (Registration) Act"
DIVORCE = "Divorce Act"
SUCCESSION = "Succession Act (as amended, including the Succession (Amendment) Act, 2022)"
ADMIN = "Administrator-General's Act"

FAMILY_TOPICS = [
    _topic(
        1,
        "family-marriage-recognition",
        "Marriage and legal recognition",
        "Marriage Act",
        _en(
            "Ugandan law recognises more than one form of marriage. A marriage "
            "is treated as legally recognised when it is celebrated according "
            "to the applicable civil, customary or religious rules.",
            "The Constitution provides for the right of men and women of "
            "eighteen years and above to marry and to found a family, and "
            "says they are entitled to equal rights in marriage, during "
            "marriage and at its dissolution.",
            "Whether your marriage is recognised affects property, children, "
            "maintenance and inheritance. Recognition depends on the type of "
            "marriage and whether legal requirements were met.",
            HELP,
            "Any marriage certificate or customary/religious record, national IDs, "
            "witness contacts.",
            f"{CONST}, Article 31; {MARRIAGE}",
            "Constitution Art. 31",
        ),
    ),
    _topic(
        2,
        "family-types-of-marriage",
        "Types of marriage",
        "Marriage Act",
        _en(
            "Ugandan law provides for civil marriage and also recognises "
            "customary and certain religious marriages when their own legal "
            "requirements are met.",
            "Different marriage types have different celebration and "
            "registration rules. Polygamy is not treated the same way in every "
            "system: customary marriage may allow more than one wife, while "
            "civil marriage is monogamous.",
            "The type of marriage you entered can change what the law expects "
            "of spouses and how a court approaches divorce or property.",
            HELP,
            "Marriage certificate, customary or religious celebration records.",
            f"{MARRIAGE}; {CUSTOMARY}",
        ),
    ),
    _topic(
        3,
        "family-marriage-registration",
        "Marriage registration",
        "Marriage Act",
        _en(
            "Registration creates an official record of a marriage. Civil "
            "marriages are recorded by the registrar. Customary marriages "
            "have a registration process under the Customary Marriage "
            "(Registration) Act.",
            "A registered record makes it easier to prove the marriage for "
            "children, property, immigration or inheritance. Failure to "
            "register does not always mean there was no marriage, but it can "
            "make proof harder.",
            "If your marriage was celebrated but not recorded, ask the "
            "registrar or a legal-aid service how to obtain or complete a record.",
            HELP,
            "Celebration evidence, IDs of spouses, witnesses, any church or "
            "customary records.",
            f"{MARRIAGE}; {CUSTOMARY}",
        ),
    ),
    _topic(
        4,
        "family-marriage-requirements",
        "Requirements for marriage",
        "Marriage Act",
        _en(
            "The Constitution sets eighteen years as the age of marriage. "
            "Other requirements depend on the marriage type and can include "
            "consent, notice, and the absence of a prohibited relationship.",
            "A person who is already in a monogamous marriage cannot validly "
            "contract another monogamous marriage. Forced marriage is not "
            "consistent with free consent.",
            "If you are unsure whether a planned marriage is allowed, get "
            "advice before the ceremony.",
            HELP,
            "Birth or ID evidence of age, any prior marriage or divorce papers.",
            f"{CONST}, Article 31; {MARRIAGE}",
            "Constitution Art. 31",
        ),
    ),
    _topic(
        5,
        "family-spouse-rights",
        "Rights and responsibilities of spouses",
        "Marriage Act",
        _en(
            "Spouses are entitled to equal rights in marriage, during marriage "
            "and at its dissolution. They also have family responsibilities "
            "towards each other and towards children.",
            "Equality in marriage is a constitutional principle. Day-to-day "
            "duties (support, care of children, respect) are also reflected "
            "in family and children legislation.",
            "If a spouse is denied dignity, safety or support, you can seek "
            "protection and legal information without waiting for a divorce.",
            HELP,
            "Marriage record, messages, evidence of support or harm.",
            f"{CONST}, Article 31; {CHILDREN}",
            "Constitution Art. 31",
        ),
    ),
    _topic(
        6,
        "family-customary-marriage",
        "Customary marriage",
        "Customary Marriage (Registration) Act",
        _en(
            "A customary marriage is celebrated according to the rites of an "
            "indigenous Ugandan community. The Customary Marriage (Registration) "
            "Act provides for registration of such marriages.",
            "Customary marriage is recognised when the community's essential "
            "rites and the Act's requirements are met. Some customary systems "
            "allow polygamy. Registration helps prove the marriage later.",
            "Disputes about bride wealth, consent or whether rites were "
            "completed should be taken to a person who understands both custom "
            "and the written law.",
            HELP,
            "Evidence of rites, clan or family witnesses, any registration paper.",
            CUSTOMARY,
        ),
    ),
    _topic(
        7,
        "family-civil-marriage",
        "Civil marriage",
        "Marriage Act",
        _en(
            "A civil marriage is celebrated before a registrar (or other "
            "authorised person) under the Marriage Act. It is a monogamous "
            "marriage.",
            "Civil marriage requires the statutory notices and formalities. "
            "A person in a subsisting civil marriage cannot lawfully enter "
            "another monogamous marriage.",
            "Keep the marriage certificate in a safe place. It is the usual "
            "proof of a civil marriage.",
            HELP,
            "Marriage certificate, IDs, notice or registrar documents.",
            MARRIAGE,
        ),
    ),
    _topic(
        8,
        "family-religious-marriage",
        "Religious marriage",
        "Marriage Act",
        _en(
            "Some religious marriages are recognised when they are celebrated "
            "under the applicable Ugandan statute (for example Christian "
            "marriage under the Marriage Act, or other recognised religious "
            "systems provided for by law).",
            "Recognition depends on the specific religious law that Uganda "
            "has given statutory effect, not only on a blessing in church or "
            "mosque. Ask whether your ceremony also completed civil or "
            "statutory formalities.",
            "If only a religious blessing took place, get advice on whether "
            "the law treats you as married.",
            HELP,
            "Religious certificate, registrar copy if any, witness contacts.",
            MARRIAGE,
        ),
    ),
    _topic(
        9,
        "family-polygamous-marriage",
        "Polygamous marriage",
        "Customary Marriage (Registration) Act",
        _en(
            "Polygamy (more than one wife) may be recognised in customary "
            "marriage where custom allows it. A monogamous civil marriage does "
            "not allow a second wife while the first marriage still exists.",
            "Taking another spouse while bound by a monogamous marriage can "
            "raise both family-law and criminal-law issues. Rights of each "
            "spouse and of children still have to be considered under the "
            "Constitution and children law.",
            "If you are unsure which system your marriage falls under, get "
            "advice before another ceremony.",
            HELP,
            "Existing marriage records, custom evidence, children's birth records.",
            f"{CUSTOMARY}; {MARRIAGE}; {CONST}, Article 31",
        ),
    ),
    _topic(
        10,
        "family-invalid-marriage",
        "Invalid or prohibited marriages",
        "Marriage Act",
        _en(
            "A ceremony may not create a valid marriage if a legal requirement "
            "was missing: for example lack of capacity or consent, a prohibited "
            "relationship, or a previous undissolved monogamous marriage.",
            "The Marriage Act and related laws set prohibited degrees and "
            "other bars. A void or voidable marriage has serious effects on "
            "status, property and children — those effects must be assessed "
            "on the facts.",
            "Do not assume a ceremony was 'not a marriage' or 'automatically "
            "void' without advice. Courts decide status disputes.",
            HELP,
            "Ceremony records, evidence of age or prior marriage, family witnesses.",
            f"{MARRIAGE}; {CONST}, Article 31",
        ),
    ),
    _topic(
        11,
        "family-divorce",
        "Divorce",
        "Divorce Act",
        _en(
            "Divorce is the legal ending of a marriage by a court. It is not "
            "the same as informal separation. The Divorce Act and related "
            "rules apply to marriages they cover; customary marriages may "
            "follow additional or different processes.",
            "A court can dissolve a marriage only on grounds and procedures "
            "the law allows. Children, property and maintenance are usually "
            "considered as part of, or alongside, the divorce.",
            "Leaving the home or agreeing to live apart does not by itself "
            "end a legal marriage.",
            HELP,
            "Marriage certificate, evidence supporting the ground, children's "
            "details, property records.",
            DIVORCE,
        ),
    ),
    _topic(
        12,
        "family-legal-separation",
        "Legal separation",
        "Divorce Act",
        _en(
            "Spouses may live apart without a divorce. A court order or a "
            "written agreement can deal with children, maintenance and "
            "property during separation.",
            "Separation does not always end the marriage. Maintenance and "
            "parental responsibility can still be enforced. The exact orders "
            "available depend on the marriage type and the court.",
            "If you need protection or child support during separation, you "
            "do not have to wait for a full divorce.",
            HELP,
            "Marriage record, any agreement, evidence of income and children's needs.",
            f"{DIVORCE}; {CHILDREN}",
        ),
    ),
    _topic(
        13,
        "family-grounds-for-divorce",
        "Grounds for divorce",
        "Divorce Act",
        _en(
            "A court does not grant divorce only because spouses no longer "
            "get along. The Divorce Act sets specific grounds. Which grounds "
            "apply depends on the kind of marriage.",
            "Typical statutory grounds have included adultery, cruelty and "
            "desertion, among others provided by law. Facts must be proved. "
            "This is general information, not a prediction of your case.",
            "A legal-aid lawyer can explain which ground, if any, fits your "
            "situation and what evidence is needed.",
            HELP,
            "Marriage certificate, evidence of the alleged ground, witness details.",
            DIVORCE,
        ),
    ),
    _topic(
        14,
        "family-divorce-procedure",
        "Divorce procedure",
        "Divorce Act",
        _en(
            "Divorce is started in court with a petition (or similar process) "
            "and served on the other spouse. The court hears evidence and "
            "may make orders about children, property and costs.",
            "Procedure follows court rules. Time limits, service and proof "
            "matter. Representing yourself is possible but risky in contested "
            "cases.",
            "Get the correct court and forms through a legal-aid clinic or "
            "the court registry rather than relying on informal 'quick divorce' "
            "offers.",
            HELP,
            "Marriage certificate, petition drafts, proof of service, children's records.",
            DIVORCE,
        ),
    ),
    _topic(
        15,
        "family-children-during-divorce",
        "Children during divorce",
        "Children Act",
        _en(
            "When parents separate or divorce, decisions about children must "
            "put the child's welfare first. Custody, care, access and "
            "maintenance can be ordered by a court.",
            "The Children Act makes the welfare of the child the guiding "
            "principle. Both parents generally keep parental responsibility "
            "unless a court orders otherwise.",
            "Do not withhold a child from the other parent as bargaining, "
            "except where there is a real safety risk — then seek urgent "
            "protection.",
            HELP,
            "Birth records, school and medical information, any protection reports.",
            f"{CHILDREN}; {CONST}, Article 34",
            "Constitution Art. 34",
        ),
    ),
    _topic(
        16,
        "family-maintenance-after-divorce",
        "Maintenance after separation or divorce",
        "Divorce Act",
        _en(
            "A spouse or child may be entitled to maintenance (financial "
            "support) during separation or after divorce, depending on the "
            "court's orders and the law that applies.",
            "Child maintenance is a parental duty under the Children Act. "
            "Spousal maintenance depends on the marriage type, need and the "
            "court's discretion under the relevant statute.",
            "If an order is ignored, enforcement through court or a probation "
            "officer may be possible. Do not rely on informal promises alone.",
            HELP,
            "Court orders, income evidence, children's expense records.",
            f"{CHILDREN}; {DIVORCE}",
        ),
    ),
    _topic(
        17,
        "family-child-rights",
        "Child rights",
        "Children Act",
        _en(
            "Every child has rights to life, education, health, name and "
            "nationality, and to be protected from abuse and neglect. The "
            "child's best interests are a primary consideration.",
            "The Constitution (Article 34) and the Children Act protect "
            "children. A child is generally a person below eighteen years.",
            "If a child's rights are at risk, report to a probation and "
            "social welfare officer, police Family and Child Protection unit, "
            "or a trusted legal-aid organisation.",
            HELP,
            "Birth record, school or medical notes, any police or probation report.",
            f"{CONST}, Article 34; {CHILDREN}",
            "Constitution Art. 34",
        ),
    ),
    _topic(
        18,
        "family-parental-responsibility",
        "Parental responsibility",
        "Children Act",
        _en(
            "Parental responsibility is the duty to care for a child: food, "
            "shelter, clothing, education, medical care and protection. It "
            "is not only for the parent the child lives with.",
            "The Children Act places responsibility on parents and, in some "
            "situations, on others with parental duties. Education and "
            "medical care are part of that responsibility.",
            "If a parent is not providing care, the other parent or a "
            "relative can seek maintenance or protection orders rather than "
            "taking the law into their own hands.",
            HELP,
            "Proof of parentage, school bills, medical bills, messages about support.",
            CHILDREN,
        ),
    ),
    _topic(
        19,
        "family-child-custody",
        "Custody of children",
        "Children Act",
        _en(
            "Custody (including care and control) is about who the child "
            "lives with and who makes day-to-day decisions. Courts decide "
            "disputes using the welfare of the child, not a parent's anger.",
            "There is no automatic rule that a child 'belongs' to the father "
            "or the mother. The Children Act requires the best interests of "
            "the child to come first.",
            "If you cannot agree, apply to the family and children court or "
            "seek mediation through probation services. Avoid grabbing or "
            "hiding the child.",
            HELP,
            "Birth record, evidence of care, school reports, any prior orders.",
            CHILDREN,
        ),
    ),
    _topic(
        20,
        "family-child-access",
        "Access and visitation",
        "Children Act",
        _en(
            "A parent who does not live with the child may still have a right "
            "to reasonable access (visitation), unless contact would harm "
            "the child.",
            "Access arrangements can be agreed or ordered by a court. The "
            "welfare principle still applies. Supervised contact can be "
            "used where safety is a concern.",
            "If access is blocked or misused, return to court or probation "
            "services rather than using force.",
            HELP,
            "Any existing order, proposed contact timetable, safety reports.",
            CHILDREN,
        ),
    ),
    _topic(
        21,
        "family-child-maintenance",
        "Child maintenance",
        "Children Act",
        _en(
            "Parents have a duty to provide for a child's needs, including "
            "food, clothing, education and healthcare, whether or not they "
            "live with the child or were married to each other.",
            "The Children Act allows applications for maintenance. Amounts "
            "depend on the child's needs and each parent's means. This is "
            "not a fine or a punishment; it is support for the child.",
            "If a parent fails to provide support, apply through the family "
            "and children court or seek help from a probation and social "
            "welfare officer or a legal-aid service.",
            HELP,
            "Birth record, proof of parentage if disputed, income evidence, "
            "school and medical bills.",
            CHILDREN,
        ),
    ),
    _topic(
        22,
        "family-child-protection",
        "Child protection",
        "Children Act",
        _en(
            "The law protects children from abuse, neglect, harmful labour "
            "and trafficking. Local authorities and police have duties to "
            "intervene when a child is at risk.",
            "The Children Act provides for care orders, supervision and "
            "other protection measures. Anyone may report a child in need "
            "of care and protection.",
            "If a child is in immediate danger, contact police or the "
            "probation office at once. Do not wait for a family meeting if "
            "the child is being harmed.",
            HELP,
            "Any medical or police report, names of people involved, the "
            "child's location.",
            f"{CHILDREN}; {CONST}, Article 34",
            "Constitution Art. 34",
        ),
    ),
    _topic(
        23,
        "family-child-abuse",
        "Child abuse",
        "Children Act",
        _en(
            "Child abuse includes physical harm, sexual abuse, emotional "
            "abuse and exploitation. It is not a private family matter when "
            "a child is being hurt.",
            "The Children Act and the Penal Code (for crimes such as "
            "defilement or assault) can both apply. A child has a right to "
            "protection regardless of who the abuser is.",
            "Report to police Family and Child Protection, a probation "
            "officer, or a hospital. The child may need medical care and a "
            "safe place to stay.",
            HELP,
            "Medical notes, photos if safe to keep, names of witnesses, "
            "any previous reports.",
            f"{CHILDREN}; {CONST}, Article 34",
        ),
    ),
    _topic(
        24,
        "family-child-neglect",
        "Child neglect",
        "Children Act",
        _en(
            "Neglect is a serious failure to provide a child's basic needs "
            "or supervision. It can be acted on even when there is no "
            "physical beating.",
            "The Children Act treats a child who is neglected as a child in "
            "need of care and protection. Poverty alone is not an excuse to "
            "abandon a child, but support services should also be considered.",
            "Report ongoing neglect to the probation office. Relatives can "
            "ask about kinship or foster arrangements through lawful channels.",
            HELP,
            "Evidence of living conditions, school absence, medical neglect.",
            CHILDREN,
        ),
    ),
    _topic(
        25,
        "family-child-abduction",
        "Child abduction",
        "Children Act",
        _en(
            "Taking or hiding a child in breach of another person's lawful "
            "care rights, or taking a child out of Uganda without required "
            "consent, can be a serious legal matter.",
            "Custody disputes must be resolved by agreement or court, not by "
            "snatching. Cross-border cases may involve additional procedures.",
            "If a child has been taken, contact police immediately and get "
            "legal help. Keep copies of birth records and any custody order.",
            HELP,
            "Birth record, custody order if any, last known location, travel "
            "information.",
            CHILDREN,
        ),
    ),
    _topic(
        26,
        "family-children-outside-marriage",
        "Children born outside marriage",
        "Children Act",
        _en(
            "A child born to unmarried parents still has rights to care, "
            "maintenance, a name and protection. Parental responsibility "
            "is not limited to children of a marriage.",
            "The Children Act focuses on the child, not on whether the "
            "parents married. Proof of paternity may be needed for some "
            "claims. Succession rules after a parent's death have been "
            "amended and should be checked with a lawyer.",
            "Register the birth. If support is refused, apply for maintenance.",
            HELP,
            "Birth notification, any acknowledgment of paternity, expense records.",
            f"{CHILDREN}; {SUCCESSION}",
        ),
    ),
    _topic(
        27,
        "family-paternity",
        "Paternity",
        "Children Act",
        _en(
            "Paternity is the legal identification of a child's father. It "
            "matters for maintenance, parental responsibility, name and "
            "inheritance.",
            "Paternity may be acknowledged, presumed in some situations, or "
            "established through court proceedings, which can include "
            "scientific testing where the court orders it.",
            "If paternity is denied, do not rely on rumours. Apply to court "
            "or seek legal aid. DNA testing is a court-supervised process, "
            "not something to force at home.",
            HELP,
            "Birth record, any written acknowledgment, messages, proposed "
            "test orders.",
            CHILDREN,
        ),
    ),
    _topic(
        28,
        "family-birth-registration",
        "Birth registration",
        "Children Act",
        _en(
            "Every child should be registered after birth. Registration "
            "supports identity, school enrolment, health care and later "
            "claims to maintenance or inheritance.",
            "The Constitution recognises every child's right to a name and "
            "nationality. Late registration is often still possible through "
            "NIRA processes.",
            "If a birth was not registered, visit a NIRA office or ask a "
            "probation officer how to apply. Do not buy fake certificates.",
            HELP,
            "Hospital birth notification, parents' IDs, any church or LC letter.",
            f"{CONST}, Article 34; {CHILDREN}",
            "Constitution Art. 34",
        ),
    ),
    _topic(
        29,
        "family-domestic-violence",
        "Domestic violence",
        "Domestic Violence Act, 2010",
        _en(
            "Domestic violence includes physical, sexual, emotional, "
            "psychological and economic abuse by a person in a domestic "
            "relationship. It is not a private matter the law ignores.",
            "The Domestic Violence Act, 2010 defines these forms of abuse "
            "and provides for protection orders, shelter information and "
            "criminal consequences where other laws are also broken.",
            "If you are in danger, go to a safe place and contact police or "
            "a domestic-violence shelter. You may apply for a protection "
            "order even if you are not ready to end the relationship.",
            HELP,
            "Medical notes, photos, threatening messages, witness names, "
            "any previous reports.",
            DVA,
        ),
        description="Includes physical, emotional, economic and sexual abuse "
        "in domestic relationships.",
    ),
    _topic(
        30,
        "family-reporting-domestic-violence",
        "Reporting domestic violence",
        "Domestic Violence Act, 2010",
        _en(
            "You can report domestic violence to the police, a local council "
            "official, or other persons authorised under the Domestic "
            "Violence Act. You do not need the abuser's permission.",
            "The Act provides for complaints, assistance and, where "
            "appropriate, arrest. Medical examination should be sought after "
            "physical or sexual violence.",
            "Ask the officer to record the complaint. Keep the reference "
            "number. A legal-aid organisation can go with you.",
            HELP,
            "Medical form (PF3 where issued), complaint number, copies of "
            "messages or photos.",
            DVA,
        ),
    ),
    _topic(
        31,
        "family-protection-orders",
        "Protection orders",
        "Domestic Violence Act, 2010",
        _en(
            "A protection order is a court order that can stop an abuser "
            "from contacting, approaching or harming you, and can include "
            "other conditions the court finds necessary.",
            "The Domestic Violence Act, 2010 allows applications for "
            "protection orders, including in urgent situations. Breaking "
            "an order can lead to arrest.",
            "Apply at the magistrate's court. Take any evidence of violence. "
            "Ask the court clerk or a legal-aid desk for the forms.",
            HELP,
            "ID, evidence of the relationship, evidence of abuse, any police "
            "reference.",
            DVA,
        ),
    ),
    _topic(
        32,
        "family-property",
        "Family property",
        "Constitution of Uganda",
        _en(
            "Property used by the family — including land and the family "
            "home — is subject to constitutional equality principles and to "
            "land and succession statutes. Ownership is not always only in "
            "the name written on one document.",
            "The Constitution guarantees equal rights in marriage. The Land "
            "Act requires spousal consent before certain family land is "
            "sold or mortgaged. Courts look at contributions and fairness; "
            "outcomes depend on facts.",
            "Do not sign away land under pressure. Get independent advice "
            "before sale, mortgage or a 'family agreement' that gives away "
            "your interest.",
            HELP,
            "Title or sales agreement, marriage record, evidence of contribution, "
            "any consent forms.",
            f"{CONST}, Article 31; Land Act, 1998",
            "Constitution Art. 31",
        ),
    ),
    _topic(
        33,
        "family-spousal-property",
        "Spousal property rights",
        "Constitution of Uganda",
        _en(
            "Spouses have equal rights in marriage, including in relation to "
            "property acquired and used during the marriage. A title in one "
            "name is not always the end of the story.",
            "Article 31 equality, Land Act consent rules for family land, "
            "and matrimonial property principles developed by courts all "
            "matter. Each case is fact-specific.",
            "If a spouse is selling land or the home without you, seek urgent "
            "legal help and consider notifying the land office.",
            HELP,
            "Marriage record, land title, receipts, messages about the property.",
            f"{CONST}, Article 31; Land Act, 1998",
        ),
    ),
    _topic(
        34,
        "family-wills",
        "Wills",
        "Succession Act",
        _en(
            "A will is a written document stating how a person wants their "
            "property shared after death. The Succession Act sets formalities "
            "for a valid will, including how it may later be changed.",
            "A will generally needs to be in writing, signed and witnessed "
            "as the Act requires. Changing a will usually means a new will "
            "or a legally valid addition (codicil), not an informal note.",
            "Ask a lawyer or the Administrator General's office how to make "
            "or update a will. Keep the original in a safe place and tell a "
            "trusted person where it is.",
            HELP,
            "Draft will, list of property, IDs of proposed executors and witnesses.",
            SUCCESSION,
        ),
    ),
    _topic(
        35,
        "family-inheritance",
        "Inheritance",
        "Succession Act",
        _en(
            "Inheritance is how property passes after death, either under a "
            "valid will or under intestacy rules when there is no valid will. "
            "Spouses and children have statutory rights that were reformed "
            "by the Succession (Amendment) Act, 2022.",
            "The Constitution and the Succession Act (as amended) protect "
            "widows, widowers and children from being left with nothing as "
            "a matter of custom alone. Exact shares depend on who survived "
            "the deceased and whether there is a will.",
            "Do not distribute an estate informally if others may have a "
            "claim. Report the death to the Administrator General where "
            "required and get legal advice.",
            HELP,
            "Death certificate, will if any, list of family members, property "
            "documents.",
            f"{SUCCESSION}; {CONST}",
        ),
    ),
    _topic(
        36,
        "family-intestacy",
        "Death without a will",
        "Succession Act",
        _en(
            "If a person dies without a valid will (intestacy), the Succession "
            "Act as amended sets out who inherits and in what shares. Custom "
            "cannot lawfully wipe out a spouse's or child's statutory rights.",
            "The 2022 succession amendments strengthened protection for "
            "spouses and children. The precise distribution depends on the "
            "surviving family. This page cannot calculate your share.",
            "Apply for letters of administration through the proper process, "
            "usually involving the Administrator General, rather than occupying "
            "property by force.",
            HELP,
            "Death certificate, family list, property list, IDs of applicants.",
            SUCCESSION,
        ),
    ),
    _topic(
        37,
        "family-probate",
        "Probate",
        "Administrator-General's Act",
        _en(
            "Probate is court authority to an executor to deal with a deceased "
            "person's estate under a will. Without probate (or letters of "
            "administration), banks and land offices will often refuse to "
            "transfer assets.",
            "The Succession Act and Administrator-General's Act set the "
            "process. Notice and inventory duties apply. Executors must act "
            "for the estate, not only for themselves.",
            "Take the will and death certificate to the Administrator "
            "General or a lawyer. Do not sell estate land before authority "
            "is granted.",
            HELP,
            "Original will, death certificate, list of assets and debts.",
            f"{SUCCESSION}; {ADMIN}",
        ),
    ),
    _topic(
        38,
        "family-letters-of-administration",
        "Letters of administration",
        "Administrator-General's Act",
        _en(
            "Letters of administration authorise a person to manage an estate "
            "when there is no executor under a valid will, or the executor "
            "cannot act. They are granted by the court after the legal "
            "process, often via the Administrator General.",
            "The Administrator-General's Act and Succession Act regulate who "
            "may apply and how beneficiaries are notified. Occupying a house "
            "is not the same as having legal authority.",
            "Start at the Administrator General's office with the death "
            "certificate and a list of the family.",
            HELP,
            "Death certificate, family introduction letter, property list, IDs.",
            f"{ADMIN}; {SUCCESSION}",
        ),
    ),
    _topic(
        39,
        "family-inheritance-disputes",
        "Family inheritance disputes",
        "Succession Act",
        _en(
            "Disputes about wills, shares, the family home or who should "
            "administer an estate are decided using the Succession Act as "
            "amended and, where relevant, land law — not by the strongest "
            "relative taking the keys.",
            "Courts can hear caveats, revocation of grants and claims by "
            "spouses or children. Mediation is often encouraged first.",
            "File a caveat or claim promptly if you fear property will be "
            "sold. Get legal aid rather than using violence.",
            HELP,
            "Will or grant documents, death certificate, evidence of your "
            "relationship, title copies.",
            SUCCESSION,
        ),
    ),
    _topic(
        40,
        "family-guardianship",
        "Guardianship",
        "Children Act",
        _en(
            "A guardian is a person with legal authority to care for a child "
            "when parents cannot. Guardianship is a court-supervised status, "
            "not an informal family title.",
            "The Children Act provides for appointment of guardians. The "
            "child's welfare is the guiding principle. Guardianship is "
            "different from adoption.",
            "Apply through the family and children court with probation "
            "officer involvement. Do not take a child across a border as a "
            "'guardian' without the proper order.",
            HELP,
            "Child's birth record, parents' death or incapacity evidence, "
            "probation report if any.",
            CHILDREN,
        ),
    ),
    _topic(
        41,
        "family-adoption",
        "Adoption",
        "Children Act",
        _en(
            "Adoption is a court order that makes a child the legal child of "
            "the adopter. It is tightly regulated, especially for "
            "inter-country adoption.",
            "The Children Act sets who may adopt, residence and probation "
            "requirements, and the need for a court order. Informal 'we "
            "have taken the child' arrangements are not adoption.",
            "Start with the probation and social welfare office. Never pay "
            "anyone to 'get you a child'.",
            HELP,
            "Applicant IDs, child's birth record, probation reports, any "
            "parental consent documents.",
            CHILDREN,
        ),
    ),
    _topic(
        42,
        "family-foster-care",
        "Foster care",
        "Children Act",
        _en(
            "Foster care is a temporary care arrangement for a child in need "
            "of care and protection, arranged through the children's "
            "authorities rather than as a private sale of a child.",
            "The Children Act provides for foster placements under "
            "supervision. Foster carers do not automatically become parents.",
            "If you wish to foster, contact the probation office. If a child "
            "has been left with you, report it so the placement can be made "
            "lawful.",
            HELP,
            "Any existing care order, child's details, your ID and home "
            "information.",
            CHILDREN,
        ),
    ),
    _topic(
        43,
        "family-kinship-care",
        "Kinship care",
        "Children Act",
        _en(
            "Relatives often care for children when parents die or cannot "
            "cope. The law still requires that the child's welfare, "
            "education and protection are met.",
            "Kinship care can be recognised through children's court or "
            "probation processes. It does not by itself transfer inheritance "
            "or allow the child to be taken abroad.",
            "Register the arrangement with the probation office so schools "
            "and clinics know who is responsible, and so the child is not "
            "treated as unaccompanied.",
            HELP,
            "Proof of kinship, parents' death or absence evidence, school letters.",
            CHILDREN,
        ),
    ),
    _topic(
        44,
        "family-elder-care",
        "Elder care and family responsibilities",
        "Constitution of Uganda",
        _en(
            "Older relatives retain dignity and property rights. Family "
            "members often provide care, but neglect, violence or grabbing "
            "an elder's land is unlawful.",
            "The Constitution protects the dignity of all persons. Domestic "
            "violence law can apply where an elder is abused in a domestic "
            "setting. Property still follows land and succession law.",
            "If an elder is being harmed or stripped of land, contact police, "
            "a legal-aid clinic or the land office. Care duties do not "
            "create a right to seize property.",
            HELP,
            "Title documents, medical notes, evidence of abuse or pressure.",
            f"{CONST}; {DVA}; Land Act, 1998",
        ),
    ),
]
