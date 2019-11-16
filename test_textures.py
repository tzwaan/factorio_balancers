from py_factorio_blueprints.entity import Direction


TEXTURES = {
    'unknown': "X",
    'empty': " ",
    'transport-belt': {
        Direction.up(): (
            ("^",),
        ),
        Direction.right(): (
            (">",),
        ),
        Direction.down(): (
            ("V",),
        ),
        Direction.left(): (
            ("<",),
        )
    },
    'splitter': {
        Direction.up(): (
            ("L", "R"),
        ),
        Direction.right(): (
            ("L",),
            ("R",),
        ),
        Direction.down(): (
            ("R", "L"),
        ),
        Direction.left(): (
            ("R",),
            ("L",),
        )
    }
}

TEXTURES_WIDE = {
    'unknown': "XX",
    'empty': "  ",
    'transport-belt': {
        Direction.up(): (
            ("/\\",),
        ),
        Direction.right(): (
            (">>",),
        ),
        Direction.down(): (
            ("\\/",),
        ),
        Direction.left(): (
            ("<<",),
        )
    },
    'splitter': {
        Direction.up(): (
            ("/-", "-\\"),
        ),
        Direction.right(): (
            ("-\\",),
            ("-/",),
        ),
        Direction.down(): (
            ("\\_", "_/"),
        ),
        Direction.left(): (
            ("/-",),
            ("\\-",),
        )
    }
}
