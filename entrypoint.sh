#!/bin/sh
# Auth GitHub optionnelle (token via env, jamais affiché)
if [ -n "$GH_TOKEN" ]; then
  git config --global url."https://oauth2:${GH_TOKEN}@github.com/".insteadOf "https://github.com/"
fi
git config --global user.name "${GIT_USER:-aurturita}"
git config --global user.email "${GIT_EMAIL:-aurturita@users.noreply.github.com}"
git config --global --add safe.directory '*'
exec "$@"
