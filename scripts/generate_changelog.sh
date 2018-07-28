#!/bin/sh

git log --no-decorate --no-merges --branches=dev --format="%ci %s" | unix2dos > CHANGES.txt
