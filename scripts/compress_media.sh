#!/usr/bin/env bash
# Shrink photos and video clips for a project page, and print the Markdown to paste.
#
#   scripts/compress_media.sh <project-slug> <file>... [--mute]
#   e.g. scripts/compress_media.sh tullomer-drone-applications ~/Documents/portfolio-intake/x/flight.mov
#
# Writes to docs/projects/<slug>/img/ and never touches the originals. Outputs carry no metadata:
# phones tag photos and clips with GPS coordinates, camera model and capture time.
#   video (mov mp4 m4v mkv webm avi) -> <name>.mp4, H.264, at most 1280 px wide, fast-start,
#                                       plus <name>.jpg poster (the PDF shows the poster instead)
#                                       --mute drops the audio (do this for silent loops)
#   photo (jpg jpeg heic png tif)    -> <name>.jpg, long edge at most 1800 px, quality 80
#   render/diagram (png)             -> kept as PNG (transparency), long edge at most 1800 px;
#                                       name it *-render.png or *-diagram.png to take this path
# Needs a recent ffmpeg (brew install ffmpeg; tested with 8.1, which applies the rotation tag before dropping it);
# photos are decoded and resized with macOS sips first, so HEIC works too.
set -euo pipefail

[[ $# -ge 2 ]] || { sed -n 2,16p "$0" | sed 's/^# \{0,1\}//'; exit 1; }
slug=$1; shift
root=$(cd "$(dirname "$0")/.." && pwd)
page="$root/docs/projects/$slug"
[[ -d $page ]] || { echo "no project page at docs/projects/$slug" >&2; exit 1; }
out="$page/img"; mkdir -p "$out"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT

audio=(-c:a aac -b:a 96k)
files=()
for arg in "$@"; do
  if [[ $arg == --mute ]]; then audio=(-an); else files+=("$arg"); fi
done

# "Flight Test 02.MOV" -> flight-test-02
slugify() { basename "${1%.*}" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-|-$//g'; }
size() { du -h "$1" | cut -f1 | tr -d ' '; }
# sips -Z would also enlarge small images, so only pass it for ones over 1800 px
fit() {
  local w h; w=$(sips -g pixelWidth "$1" | awk '/pixelWidth/ {print $2}'); h=$(sips -g pixelHeight "$1" | awk '/pixelHeight/ {print $2}')
  (( w > 1800 || h > 1800 )) && echo -Z 1800 || true
}

for f in "${files[@]}"; do
  [[ -f $f ]] || { echo "skip (not a file): $f" >&2; continue; }
  name=$(slugify "$f")
  ext=$(echo "${f##*.}" | tr '[:upper:]' '[:lower:]')
  case $ext in
    mov|mp4|m4v|mkv|webm|avi)
      # first video and audio stream only: iPhone clips also carry location/metadata tracks
      ffmpeg -v error -y -i "$f" -map 0:v:0 -map "0:a:0?" -map_metadata -1 -map_chapters -1 \
        -vf "scale='min(1280,iw)':-2,format=yuv420p" \
        -c:v libx264 -preset slow -crf 26 -movflags +faststart "${audio[@]}" "$out/$name.mp4"
      # poster from 1 s in (or the first frame of anything shorter)
      ffmpeg -v error -y -ss 1 -i "$f" -frames:v 1 -map_metadata -1 -vf "scale='min(1280,iw)':-2" -q:v 3 "$out/$name.jpg" 2>/dev/null ||
        ffmpeg -v error -y -i "$f" -frames:v 1 -map_metadata -1 -vf "scale='min(1280,iw)':-2" -q:v 3 "$out/$name.jpg"
      echo "$f -> img/$name.mp4 ($(size "$out/$name.mp4")) + img/$name.jpg"
      if [[ ${audio[0]} == -an ]]; then attrs='autoplay loop muted playsinline'; else attrs='controls preload="none" playsinline'; fi
      cat <<EOF
    <figure>
    <video src="img/$name.mp4" poster="img/$name.jpg" $attrs></video>
    <figcaption>Caption</figcaption>
    </figure>

EOF
      ;;
    png|jpg|jpeg|heic|heif|tif|tiff)
      # sips decodes (HEIC too) and resizes to a lossless PNG; ffmpeg applies the rotation tag and
      # writes the output without any metadata
      sips -s format png $(fit "$f") "$f" --out "$tmp/$name.png" >/dev/null
      if [[ $ext == png && $name =~ -(render|diagram)$ ]]; then target="$out/$name.png"
        ffmpeg -v error -y -i "$tmp/$name.png" -map_metadata -1 "$target"
      else target="$out/$name.jpg"
        ffmpeg -v error -y -i "$tmp/$name.png" -map_metadata -1 -q:v 4 "$target"
      fi
      echo "$f -> img/$(basename "$target") ($(size "$target"))"
      cat <<EOF
    <figure markdown="span">
      ![Alt text](img/$(basename "$target"))
      <figcaption>Caption</figcaption>
    </figure>

EOF
      ;;
    *) echo "skip (unknown type .$ext): $f" >&2 ;;
  esac
done
