"""Phone number intelligence: region, carrier and line type (no external API)."""

import phonenumbers
from phonenumbers import NumberParseException, carrier, geocoder

_LINE_TYPES = {
    phonenumbers.PhoneNumberType.FIXED_LINE: "Fixed line",
    phonenumbers.PhoneNumberType.MOBILE: "Mobile",
    phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed line or mobile",
    phonenumbers.PhoneNumberType.TOLL_FREE: "Toll-free",
    phonenumbers.PhoneNumberType.PREMIUM_RATE: "Premium rate",
    phonenumbers.PhoneNumberType.SHARED_COST: "Shared cost",
    phonenumbers.PhoneNumberType.VOIP: "VoIP",
    phonenumbers.PhoneNumberType.PERSONAL_NUMBER: "Personal number",
    phonenumbers.PhoneNumberType.PAGER: "Pager",
    phonenumbers.PhoneNumberType.UAN: "UAN",
    phonenumbers.PhoneNumberType.VOICEMAIL: "Voicemail",
    phonenumbers.PhoneNumberType.UNKNOWN: "Unknown",
}


def analyze_phone(raw_number):
    try:
        parsed = phonenumbers.parse(raw_number, None)
    except NumberParseException as exc:
        return {
            "source": "phonenumbers",
            "status": "error",
            "error": f"Invalid phone number ({exc}). Use international format with '+', e.g. +34 612345678.",
        }

    if not phonenumbers.is_valid_number(parsed):
        return {
            "source": "phonenumbers",
            "status": "error",
            "error": "The number is not valid for its region/format.",
        }

    line_type = _LINE_TYPES.get(phonenumbers.number_type(parsed), "Unknown")

    return {
        "source": "phonenumbers",
        "status": "ok",
        "e164": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
        "country": geocoder.description_for_number(parsed, "en") or "Unknown",
        "carrier": carrier.name_for_number(parsed, "en") or "Unknown",
        "line_type": line_type,
    }
