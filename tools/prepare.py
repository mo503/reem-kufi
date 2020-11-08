import argparse

from datetime import datetime
from glyphsLib.classes import GSFont


def merge(args):
    arabic = GSFont(args.arabicfile)
    latin = GSFont(args.latinfile)

    unicodes = set()
    for glyph in arabic.glyphs:
        unicodes.update(glyph.unicodes)

    masters = {m.name: m for m in arabic.masters}

    for glyph in latin.glyphs:
        name = glyph.name
        if name in ("space", "nbspace", "CR", "NULL", ".notdef"):
            continue

        # We don’t want the ligatures, they are useless in this design.
        if name.startswith("f_") or name in {"fi", "fl"}:
            continue
        assert glyph.name not in arabic.glyphs, glyph.name
        assert not (
            glyph.unicodes and set(glyph.unicodes).issubset(unicodes)
        ), glyph.unicodes
        for layer in glyph.layers:
            if (
                layer.master.name in masters
                and layer.layerId == layer.associatedMasterId
            ):
                layer.layerId = masters[layer.master.name].id
                layer.associatedMasterId = layer.layerId

        arabic.glyphs.append(glyph)

    # Copy kerning and groups.
    for master in arabic.masters:
        for other in latin.masters:
            if master.name == other.name:
                if master.id in arabic.kerning:
                    arabic.kerning[master.id].update(latin.kerning[other.id])
                else:
                    arabic.kerning[master.id] = latin.kerning[other.id]
                master.xHeight = other.xHeight
                master.capHeight = other.capHeight
                continue

    # Merge Arabic and Latin features, making sure languagesystem statements
    # come first.
    for klass in latin.classes:
        arabic.classes.append(klass)
    for prefix in latin.featurePrefixes:
        if prefix.name == "Languagesystems":
            arabic.featurePrefixes[prefix.name].code += prefix.code
            arabic.featurePrefixes[prefix.name].code = "\n".join(
                sorted(arabic.featurePrefixes[prefix.name].code.split("\n"))
            )
            continue
        arabic.featurePrefixes.append(prefix)
    for feature in latin.features:
        if feature.name in {"liga", "dlig"}:
            continue
        arabic.features.append(feature)

    # Set metadata
    arabic.versionMajor, arabic.versionMinor = map(int, args.version.split("."))
    year = datetime.now().year
    arabic.copyright = f"Copyright © 2015-{year} The Reem Kufi Project Authors."

    return arabic


def main():
    parser = argparse.ArgumentParser(description="Build Reem Kufi fonts.")
    parser.add_argument("arabicfile", metavar="FILE", help="input font to process")
    parser.add_argument("latinfile", metavar="FILE", help="input font to process")
    parser.add_argument(
        "--out-file", metavar="FILE", help="output font to write", required=True
    )
    parser.add_argument(
        "--version", metavar="version", help="version number", required=True
    )

    args = parser.parse_args()

    font = merge(args)
    font.save(args.out_file)


if __name__ == "__main__":
    main()
