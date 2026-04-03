from __future__ import annotations


def translate_legacy_args(argv: list[str]) -> list[str]:
    if not argv:
        return argv
    if argv[0].startswith("-"):
        if "--find" in argv:
            index = argv.index("--find")
            output = ["find"]
            if index + 1 < len(argv) and not argv[index + 1].startswith("-"):
                output.append(argv[index + 1])
            for item in argv:
                if item == "--find":
                    continue
                if index + 1 < len(argv) and item == argv[index + 1] and not item.startswith("-"):
                    continue
                output.append(item)
            return output
        if "--bulk" in argv:
            index = argv.index("--bulk")
            output = ["create", "--bulk"]
            if index + 1 < len(argv):
                output.append(argv[index + 1])
            for offset, item in enumerate(argv):
                if item == "--bulk":
                    continue
                if offset == index + 1:
                    continue
                output.append(item)
            return output
        if "--interactive" in argv:
            return ["create", *[item for item in argv if item != "--interactive"]]
    return argv
