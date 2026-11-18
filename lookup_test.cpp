// Host test for graphics::JapaneseFont::lookup. Build from the firmware checkout root:
//   g++ -std=c++17 -include cstdint -DOLED_JA -DPROGMEM= -I src lookup_test.cpp src/graphics/fonts/OLEDDisplayFontsJA.cpp
//   ./a.out "りょうかい。12℃" -> prints the font index of each displayed glyph
#define OLED_JA
#define PROGMEM
#include <cstdio>
#include <cstring>
#include <cstdint>
#include "graphics/JapaneseFont.h"
#include "graphics/fonts/OLEDDisplayFontsJA.h"
int main(int argc, char **argv) {
    for (int a = 1; a < argc; a++) {
        const char *s = argv[a];
        for (size_t i = 0; i < strlen(s); i++) {
            char c = graphics::JapaneseFont::lookup((uint8_t)s[i]);
            if (c) printf("%02X ", (uint8_t)c);
        }
        printf("\n");
    }

}
