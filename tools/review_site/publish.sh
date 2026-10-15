#!/bin/sh
# Encode finished frame folders into the site, rebuild site.json, commit and push (Vercel deploys on push).
R=/tmp/claude-0/-home-claude-site-10/339d885c-9635-527f-8aeb-f861000ea518/scratchpad/review
S=/home/claude/review-site
for d in $R/frames2/*/*/; do
  [ -f "$d/done" ] || continue
  key=$(basename $(dirname $d)); name=$(basename $d); mkdir -p $S/media/$key
  case $name in
    *-still) out=$S/media/$key/${name%-still}.jpg; [ -f "$out" ] || ffmpeg -y -loglevel error -i $d/f000.png -q:v 3 "$out";;
    *) out=$S/media/$key/$name.mp4; fps=$(cat $d/done)
       [ -f "$out" ] || ffmpeg -y -loglevel error -framerate $fps -i $d/f%03d.png -c:v libx264 -pix_fmt yuv420p -crf 27 -preset slow -movflags +faststart "$out";;
  esac
done
for f in $R/models2/*/*.gltf.json; do [ -f "$f" ] || continue; key=$(basename $(dirname $f)); mkdir -p $S/media/$key; cp --update=none $f $S/media/$key/; done
python3 /home/claude/review-tools/gen_site.py
cd $S && git add -A && git commit -qm "Review site: add rendered takes ($1)" && git push -q origin review-site 2>&1 | tail -1
