#pragma once
#ifdef OLED_JA

#include <stdint.h>

// UTF-8 to OLEDDisplayFontsJA index: kana are shown as half-width katakana, voiced kana use a
// pre-combined glyph so one character always yields one glyph, anything else becomes U+3013.
namespace graphics
{
namespace JapaneseFont
{

static constexpr uint8_t GETA = 0x9A;    // U+3013, placeholder for undisplayable characters
static constexpr uint8_t DEGREE = 0x9B;  // U+00B0
static constexpr uint8_t CELSIUS = 0x9C; // U+2103, drawn as degree sign + C

// Index for katakana U+30A1..U+30F6; hiragana U+3041..U+3096 share it
static const uint8_t KANA_TABLE[] = {
    0xA7, 0xB1, 0xA8, 0xB2, 0xA9, 0xB3, 0xAA, 0xB4, 0xAB, 0xB5, // ァアィイゥウェエォオ
    0xB6, 0x80, 0xB7, 0x81, 0xB8, 0x82, 0xB9, 0x83, 0xBA, 0x84, // カガキギクグケゲコゴ
    0xBB, 0x85, 0xBC, 0x86, 0xBD, 0x87, 0xBE, 0x88, 0xBF, 0x89, // サザシジスズセゼソゾ
    0xC0, 0x8A, 0xC1, 0x8B, 0xAF, 0xC2, 0x8C, 0xC3, 0x8D, 0xC4, // タダチヂッツヅテデト
    0x8E, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9, 0xCA, 0x8F, 0x94, 0xCB, // ドナニヌネノハバパヒ
    0x90, 0x95, 0xCC, 0x91, 0x96, 0xCD, 0x92, 0x97, 0xCE, 0x93, // ビピフブプヘベペホボ
    0x98, 0xCF, 0xD0, 0xD1, 0xD2, 0xD3, 0xAC, 0xD4, 0xAD, 0xD5, // ポマミムメモャヤュユ
    0xAE, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xDB, 0xDC, 0xDC, 0xB2, // ョヨラリルレロヮワヰ
    0xB4, 0xA6, 0xDD, 0x99, 0xB6, 0xB9,                         // ヱヲンヴヵヶ
};

static inline uint8_t codepointToIndex(uint32_t cp)
{
    if (cp >= 0xFF61 && cp <= 0xFF9F) // half-width katakana
        return (uint8_t)(0xA1 + (cp - 0xFF61));
    if (cp >= 0x30A1 && cp <= 0x30F6) // katakana
        return KANA_TABLE[cp - 0x30A1];
    if (cp >= 0x3041 && cp <= 0x3096) // hiragana
        return KANA_TABLE[cp - 0x3041];
    if (cp >= 0xFF01 && cp <= 0xFF5E) // full-width ASCII
        return (uint8_t)(cp - 0xFEE0);
    if (cp >= 0x00E0 && cp <= 0x00FF) // Latin-1 lowercase letters
        return (uint8_t)cp;
    switch (cp) {
    case 0x3000: // ideographic space
    case 0x00A0: // no-break space
        return ' ';
    case 0x3001: // ideographic comma
        return 0xA4;
    case 0x3002: // ideographic full stop
        return 0xA1;
    case 0x300C: // left corner bracket
        return 0xA2;
    case 0x300D: // right corner bracket
        return 0xA3;
    case 0x30FB: // katakana middle dot
        return 0xA5;
    case 0x30FC: // prolonged sound mark
        return 0xB0;
    case 0x309B: // katakana-hiragana voiced sound mark
    case 0x3099:
        return 0xDE;
    case 0x309C: // katakana-hiragana semi-voiced sound mark
    case 0x309A:
        return 0xDF;
    case 0x00B0:
        return DEGREE;
    case 0x2103:
        return CELSIUS;
    case 0x301C: // wave dash
        return '~';
    }
    return GETA;
}

// Called once per byte of a UTF-8 string; returns the glyph index, or 0 while a character is incomplete.
static inline char lookup(const uint8_t ch)
{
    static uint32_t codepoint;
    static uint8_t remaining; // continuation bytes still expected

    if (ch < 0x80) { // ASCII
        remaining = 0;
        return (char)ch;
    }
    if (ch >= 0xC0) {     // lead byte of a multi-byte sequence
        if (ch >= 0xF8) { // invalid lead byte
            remaining = 0;
            return (char)GETA;
        }
        remaining = (ch >= 0xF0) ? 3 : (ch >= 0xE0) ? 2 : 1;
        codepoint = ch & ((ch >= 0xF0) ? 0x07 : (ch >= 0xE0) ? 0x0F : 0x1F);
        return 0;
    }
    // continuation byte
    if (remaining == 0) // stray continuation byte, already counted as part of a broken sequence
        return 0;
    codepoint = (codepoint << 6) | (ch & 0x3F);
    if (--remaining > 0)
        return 0;
    return (char)codepointToIndex(codepoint);
}

} // namespace JapaneseFont
} // namespace graphics

#endif // OLED_JA
