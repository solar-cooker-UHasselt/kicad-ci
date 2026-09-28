#!/bin/sh
# Run KiBot with the board's config.kibot.yml, or the kicad-ci default when there is none.
#
# Usage: sh run.sh, from the board repo's root, where kibot is installed.

# The default config comes with this script, in the same folder. An absolute path,
# so a board config that imports it finds it from anywhere.
here=$(cd "$(dirname "$0")" && pwd)
default="$here/default.kibot.yml"

# A board's own config.kibot.yml wins. Without one, use the default.
if [ -f config.kibot.yml ]; then
  config=config.kibot.yml
else
  config="$default"
fi
echo "KiBot config: $config"

# -E defines @KICAD_CI_DEFAULT@, so a board config can import the default.
kibot -c "$config" -E KICAD_CI_DEFAULT="$default"
