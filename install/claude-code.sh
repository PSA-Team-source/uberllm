#!/bin/sh
# UberLLM installer for Claude Code — https://uberllm.dev
#
# Points Claude Code at the UberLLM gateway. The key is saved to a file only you
# can read (~/.uberllm/key…, mode 600) and Claude Code reads it through
# apiKeyHelper; the settings file gets ANTHROPIC_BASE_URL and that helper.
# Re-runnable, reversible with --uninstall, and it backs up a settings file
# before touching it.
#
#   curl -fsSL https://uberllm.dev/install/claude-code.sh | sh                  # every project
#   curl -fsSL https://uberllm.dev/install/claude-code.sh | sh -s -- --project  # this project only
#
# Everything lives inside main(), invoked on the last line, so a download that
# is cut off part-way through executes nothing at all.
set -eu

ULL_API_BASE='https://api.uberllm.dev'
ULL_SITE='https://uberllm.dev'
ULL_KEY=''
ULL_MODEL=''
ULL_HAIKU=''
ULL_PROFILE='claude-native'

ACTION=install
ASSUME_YES=0
SCOPE=user
PROJECT_DIR=''

# ---------------------------------------------------------------- output ----

if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
  C_RESET=$(printf '\033[0m'); C_DIM=$(printf '\033[2m')
  C_BOLD=$(printf '\033[1m'); C_RED=$(printf '\033[31m')
  C_GREEN=$(printf '\033[32m'); C_YELLOW=$(printf '\033[33m')
else
  C_RESET=''; C_DIM=''; C_BOLD=''; C_RED=''; C_GREEN=''; C_YELLOW=''
fi

say()  { printf '%s\n' "$*"; }
info() { printf '  %s\n' "$*"; }
ok()   { printf '  %s✓%s %s\n' "$C_GREEN" "$C_RESET" "$*"; }
warn() { printf '  %s!%s %s\n' "$C_YELLOW" "$C_RESET" "$*" >&2; }
die()  { printf '\n  %serror%s %s\n\n' "$C_RED" "$C_RESET" "$*" >&2; exit 1; }

have() { command -v "$1" >/dev/null 2>&1; }

# ------------------------------------------------------------------ json ----

# We need a real JSON parser: settings.json belongs to the user and may already
# hold hooks, permissions and MCP servers, so it has to be merged rather than
# overwritten. sed would corrupt it. python3 and node cover effectively every
# machine that runs Claude Code; without either we print the exact block to
# paste rather than guessing.
JSON_RT=''
detect_json_runtime() {
  if have python3; then JSON_RT=python3
  elif have node; then JSON_RT=node
  fi
}

# json_get <json-string> <key> — reads one top-level string field.
json_get() {
  _json=$1; _key=$2
  case "$JSON_RT" in
    python3)
      printf '%s' "$_json" | python3 -c 'import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
v = d.get(sys.argv[1]) if isinstance(d, dict) else None
print(v if isinstance(v, str) else "")' "$_key"
      ;;
    node)
      printf '%s' "$_json" | node -e '
let s = "";
process.stdin.on("data", (c) => (s += c));
process.stdin.on("end", () => {
  let d;
  try { d = JSON.parse(s); } catch { return; }
  const v = d && typeof d === "object" ? d[process.argv[1]] : undefined;
  process.stdout.write(typeof v === "string" ? v : "");
});' "$_key"
      ;;
  esac
}

# settings_merge <path> <key> <value> [<key> <value> ...]
# Keys go into the "env" block; a key written "@name" is a top-level setting
# (apiKeyHelper). An empty value removes the key. Writes atomically via a temp file so an
# interrupted run can never leave a half-written settings.json behind.
settings_merge() {
  _path=$1; shift
  case "$JSON_RT" in
    python3)
      python3 -c 'import json, os, sys
path, pairs = sys.argv[1], sys.argv[2:]
try:
    with open(path) as f:
        cfg = json.load(f)
except Exception:
    cfg = {}
if not isinstance(cfg, dict):
    cfg = {}
env = cfg.get("env")
if not isinstance(env, dict):
    env = {}
it = iter(pairs)
for k, v in zip(it, it):
    d = env
    if k.startswith("@"):
        d, k = cfg, k[1:]
    if v == "":
        d.pop(k, None)
    else:
        d[k] = v
if env:
    cfg["env"] = env
else:
    cfg.pop("env", None)
os.makedirs(os.path.dirname(path), exist_ok=True)
tmp = path + ".uberllm.tmp"
with open(tmp, "w") as f:
    json.dump(cfg, f, indent=2)
    f.write("\n")
os.replace(tmp, path)' "$_path" "$@"
      ;;
    node)
      node -e '
const fs = require("fs"), path = require("path");
const [file, ...pairs] = process.argv.slice(1);
let cfg = {};
try { cfg = JSON.parse(fs.readFileSync(file, "utf8")); } catch {}
if (cfg === null || typeof cfg !== "object" || Array.isArray(cfg)) cfg = {};
let env = cfg.env;
if (env === null || typeof env !== "object" || Array.isArray(env)) env = {};
for (let i = 0; i < pairs.length; i += 2) {
  let k = pairs[i], d = env;
  const v = pairs[i + 1];
  if (k.startsWith("@")) { d = cfg; k = k.slice(1); }
  if (v === "") delete d[k]; else d[k] = v;
}
if (Object.keys(env).length) cfg.env = env; else delete cfg.env;
fs.mkdirSync(path.dirname(file), { recursive: true });
const tmp = file + ".uberllm.tmp";
fs.writeFileSync(tmp, JSON.stringify(cfg, null, 2) + "\n");
fs.renameSync(tmp, file);' "$_path" "$@"
      ;;
  esac
}

# ------------------------------------------------------------- discovery ----

settings_path() {
  if [ "$SCOPE" = project ]; then
    printf '%s/.claude/settings.local.json' "$PROJECT_DIR"
  elif [ -n "${CLAUDE_CONFIG_DIR:-}" ]; then
    printf '%s/settings.json' "$CLAUDE_CONFIG_DIR"
  else
    printf '%s/.claude/settings.json' "$HOME"
  fi
}

# key_path — where the key is kept: one file for the user-wide setup, one per
# project (named after the folder) so each project can carry its own key.
key_path() {
  if [ "$SCOPE" = project ]; then
    _sum=$(printf '%s' "$PROJECT_DIR" | cksum | cut -d' ' -f1)
    printf '%s/.uberllm/key-%s-%s' "$HOME" "$(basename "$PROJECT_DIR" | tr -c 'A-Za-z0-9._-
' '_')" "$_sum"
  else
    printf '%s/.uberllm/key' "$HOME"
  fi
}

# write_key <path> — saves the key readable by this user only (dir 700, file 600).
write_key() {
  _kp=$1
  (umask 077; mkdir -p "$(dirname "$_kp")"; printf '%s
' "$ULL_KEY" > "$_kp.tmp" && mv "$_kp.tmp" "$_kp")
  chmod 600 "$_kp"
}

backup_settings() {
  _path=$1
  [ -f "$_path" ] || return 0
  _stamp=$(date +%Y%m%d%H%M%S 2>/dev/null || echo backup)
  cp "$_path" "$_path.bak-$_stamp"
  info "Backed up existing settings to $C_DIM$_path.bak-$_stamp$C_RESET"
}

# ------------------------------------------------------- browser linking ----

open_browser() {
  _url=$1
  if have open; then open "$_url" >/dev/null 2>&1 || true
  elif have xdg-open; then xdg-open "$_url" >/dev/null 2>&1 || true
  fi
}

# device_link fills ULL_KEY by asking the user to approve in a browser. This is
# the path for someone who pasted the one-liner without an account.
device_link() {
  _label=$(hostname 2>/dev/null || echo "this machine")
  _platform=$(uname -s 2>/dev/null || echo unknown)

  _start=$(curl -fsS -X POST "$ULL_API_BASE/api/v1/cli/link/start" \
    -H 'content-type: application/json' \
    -d "{\"client_name\":\"$_label\",\"client_platform\":\"$_platform\"}" 2>/dev/null) \
    || die "Could not reach $ULL_API_BASE. Check your connection and try again."

  _code=$(json_get "$_start" link_code)
  _device=$(json_get "$_start" device_code)
  _url=$(json_get "$_start" verification_url)
  [ -n "$_device" ] || die "The gateway did not return a link code. Try again shortly."

  say ""
  say "  Connect Claude Code to your UberLLM account — open this link, sign in, press Connect:"
  say ""
  say "    $C_BOLD$_url$C_RESET"
  say ""
  say "    Your code: $C_BOLD$_code$C_RESET"
  say ""
  info "Opening your browser… (waiting for you to connect, Ctrl-C to cancel)"
  open_browser "$_url"

  # 15 minutes at the interval the server advertises.
  _n=0
  while [ "$_n" -lt 300 ]; do
    sleep 3
    _n=$((_n + 1))
    _poll=$(curl -fsS -X POST "$ULL_API_BASE/api/v1/cli/link/poll" \
      -H 'content-type: application/json' \
      -d "{\"device_code\":\"$_device\"}" 2>/dev/null) || continue
    _status=$(json_get "$_poll" status)
    case "$_status" in
      approved)
        ULL_KEY=$(json_get "$_poll" api_key)
        _base=$(json_get "$_poll" base_url)
        [ -n "$_base" ] && ULL_API_BASE=$_base
        [ -n "$ULL_KEY" ] || die "Approval succeeded but no key was returned. Please try again."
        ok "Connected."
        return 0
        ;;
      denied)  die "The request was denied in the browser. Nothing was changed." ;;
      expired) die "The link expired. Run the installer again to get a fresh code." ;;
    esac
  done
  die "Timed out waiting for approval. Nothing was changed."
}

# ---------------------------------------------------------------- verify ----

verify_key() {
  _body='{"model":"claude-haiku-4-5","max_tokens":1,"messages":[{"role":"user","content":"."}]}'
  _out=$(curl -fsS -X POST "$ULL_API_BASE/v1/messages" \
    -H "Authorization: Bearer $ULL_KEY" \
    -H 'anthropic-version: 2023-06-01' \
    -H 'content-type: application/json' \
    -d "$_body" 2>/dev/null) || return 1
  case "$_out" in
    *'"content"'*) return 0 ;;
    *) return 1 ;;
  esac
}

# --------------------------------------------------------------- actions ----

do_install() {
  _path=$(settings_path)
  _keyfile=$(key_path)

  if [ -z "$ULL_KEY" ]; then
    have curl || die "curl is required to link this machine."
    device_link
  fi

  say ""
  write_key "$_keyfile"
  info "Saved the key to $C_DIM$_keyfile$C_RESET (only you can read it)"
  info "Writing $C_DIM$_path$C_RESET"
  backup_settings "$_path"

  # Model discovery surfaces the gateway's own Claude builds in /model. The
  # profile decides whether we pin anything: the native profile deliberately
  # pins nothing, so Claude Code keeps asking for its own model ids and the
  # gateway maps them — which is what makes it behave exactly as before.
  # The key is read through apiKeyHelper, so any old plain-text token is removed.
  settings_merge "$_path" \
    ANTHROPIC_BASE_URL "$ULL_API_BASE" \
    ANTHROPIC_AUTH_TOKEN "" \
    @apiKeyHelper "cat \"$_keyfile\"" \
    CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY "1" \
    ANTHROPIC_MODEL "$ULL_MODEL" \
    ANTHROPIC_DEFAULT_OPUS_MODEL "$ULL_MODEL" \
    ANTHROPIC_DEFAULT_SONNET_MODEL "$ULL_MODEL" \
    ANTHROPIC_DEFAULT_HAIKU_MODEL "$ULL_HAIKU" \
    CLAUDE_CODE_SUBAGENT_MODEL "$ULL_MODEL"

  ok "Configured Claude Code."

  if have curl; then
    if verify_key; then
      ok "Verified a live request through the gateway."
    else
      warn "Settings were written, but a test request did not succeed."
      warn "Check your balance at $ULL_SITE/dashboard/credits and run 'claude' to see the error."
    fi
  fi

  # Claude Code uses ANTHROPIC_AUTH_TOKEN and ANTHROPIC_API_KEY before
  # apiKeyHelper, so a shell export of either would replace the saved key.
  for _v in ANTHROPIC_AUTH_TOKEN ANTHROPIC_API_KEY ANTHROPIC_BASE_URL ANTHROPIC_MODEL; do
    if [ -n "$(printenv "$_v" 2>/dev/null)" ]; then
      warn "$_v is set in your shell. Remove it (unset $_v, and delete it from your shell profile) so these settings are used."
    fi
  done

  if ! have claude; then
    say ""
    warn "Claude Code isn't installed yet. Install it, then run 'claude':"
    info "  npm install -g @anthropic-ai/claude-code"
  fi

  say ""
  if [ "$SCOPE" = project ]; then
    say "  ${C_BOLD}Done.${C_RESET} Restart Claude Code in $PROJECT_DIR — that project now runs on UberLLM; others are unchanged."
  else
    say "  ${C_BOLD}Done.${C_RESET} Restart Claude Code (quit it, then run 'claude') — it now runs on UberLLM."
  fi
  say ""
  info "The cost Claude Code shows is its own estimate, not your bill. What you pay is on the dashboard."
  info "Usage and balance: $C_DIM$ULL_SITE/dashboard/activity$C_RESET"
  if [ "$SCOPE" = project ]; then
    info "Undo any time:     $C_DIM""curl -fsSL $ULL_SITE/install/claude-code.sh | sh -s -- --project '$PROJECT_DIR' --uninstall$C_RESET"
  else
    info "Undo any time:     $C_DIM""curl -fsSL $ULL_SITE/install/claude-code.sh | sh -s -- --uninstall$C_RESET"
  fi
  say ""
}

do_uninstall() {
  _path=$(settings_path)
  [ -f "$_path" ] || die "No settings file at $_path — nothing to undo."

  backup_settings "$_path"
  # apiKeyHelper is removed only when it is ours (it reads a ~/.uberllm key file).
  _helper=''
  case "$(cat "$_path" 2>/dev/null)" in
    *'.uberllm/key'*) _helper='@apiKeyHelper' ;;
  esac
  settings_merge "$_path" \
    ANTHROPIC_BASE_URL "" \
    ANTHROPIC_AUTH_TOKEN "" \
    ANTHROPIC_MODEL "" \
    ANTHROPIC_DEFAULT_OPUS_MODEL "" \
    ANTHROPIC_DEFAULT_SONNET_MODEL "" \
    ANTHROPIC_DEFAULT_HAIKU_MODEL "" \
    CLAUDE_CODE_SUBAGENT_MODEL "" \
    CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY "" \
    ${_helper:+"$_helper"} ${_helper:+""}
  _keyfile=$(key_path)
  [ -f "$_keyfile" ] && rm -f "$_keyfile"

  say ""
  ok "Removed the UberLLM settings from $_path"
  info "Claude Code will use your Anthropic login again on next start."
  info "Revoke the key at $C_DIM$ULL_SITE/dashboard/keys$C_RESET"
  say ""
}

do_print() {
  say ""
  say "  1. Save your ull_ key to $(key_path) and make it private:"
  say "       chmod 600 $(key_path)"
  say "  2. Add this to $(settings_path):"
  say ""
  say "  {"
  say "    \"apiKeyHelper\": \"cat $(key_path)\","
  say "    \"env\": {"
  say "      \"ANTHROPIC_BASE_URL\": \"$ULL_API_BASE\""
  say "    }"
  say "  }"
  say ""
}

usage() {
  say "UberLLM installer for Claude Code"
  say ""
  say "  --project [DIR]  set up only this project (DIR, default: the current folder),"
  say "                   in DIR/.claude/settings.local.json; other projects are unchanged"
  say "  --uninstall      remove the settings this installer wrote (add --project for a project)"
  say "  --print          show the settings block instead of writing it"
  say "  --key KEY        use a specific ull_ key and skip browser approval"
  say "  --yes            don't prompt"
  say ""
}

main() {
  while [ $# -gt 0 ]; do
    case "$1" in
      --uninstall) ACTION=uninstall ;;
      --print)     ACTION=print ;;
      --yes|-y)    ASSUME_YES=1 ;;
      --key)       shift; [ $# -gt 0 ] || die "--key needs a value"; ULL_KEY=$1 ;;
      --key=*)     ULL_KEY=${1#--key=} ;;
      --project)   SCOPE=project
                   case "${2:-}" in ''|-*) ;; *) shift; PROJECT_DIR=$1 ;; esac ;;
      --project=*) SCOPE=project; PROJECT_DIR=${1#--project=} ;;
      -h|--help)   usage; exit 0 ;;
      *)           die "Unknown option: $1" ;;
    esac
    shift
  done

  # Allow the key to arrive by environment too, which keeps it out of the
  # process list on a shared machine.
  [ -n "${UBERLLM_API_KEY:-}" ] && ULL_KEY=$UBERLLM_API_KEY

  if [ "$SCOPE" = project ]; then
    [ -n "$PROJECT_DIR" ] || PROJECT_DIR=$(pwd)
    [ -d "$PROJECT_DIR" ] || die "No folder at $PROJECT_DIR."
    PROJECT_DIR=$(cd "$PROJECT_DIR" && pwd)
    [ "$PROJECT_DIR" != "$HOME" ] || die "That is your home folder. Run this inside a project, or drop --project to set up every project."
  fi

  say ""
  say "  ${C_BOLD}UberLLM${C_RESET} → Claude Code"

  if [ "$ACTION" = print ]; then do_print; exit 0; fi

  detect_json_runtime
  if [ -z "$JSON_RT" ]; then
    warn "Neither python3 nor node was found, so settings.json can't be merged safely."
    do_print
    exit 1
  fi

  case "$ACTION" in
    install)   do_install ;;
    uninstall) do_uninstall ;;
  esac
}

main "$@"
